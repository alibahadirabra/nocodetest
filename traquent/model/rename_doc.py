# Copyright (c) 2022, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
from types import NoneType
from typing import TYPE_CHECKING

import traquent
import traquent.permissions
from traquent import _, bold
from traquent.model.document import Document
from traquent.model.dynamic_links import get_dynamic_link_map
from traquent.model.naming import validate_name
from traquent.model.utils.user_settings import sync_user_settings, update_user_settings_data
from traquent.query_builder import Field
from traquent.utils.data import sbool
from traquent.utils.password import rename_password
from traquent.utils.scheduler import is_scheduler_inactive

if TYPE_CHECKING:
	from traquent.model.meta import Meta


@traquent.whitelist()
def update_document_title(
	*,
	doctype: str,
	docname: str,
	title: str | None = None,
	name: str | None = None,
	merge: bool = False,
	enqueue: bool = False,
	**kwargs,
) -> str:
	"""
	Update the name or title of a document. Return `name` if document was renamed, `docname` if renaming operation was queued.

	:param doctype: DocType of the document
	:param docname: Name of the document
	:param title: New Title of the document
	:param name: New Name of the document
	:param merge: Merge the current Document with the existing one if exists
	:param enqueue: Enqueue the rename operation, title is updated in current process
	"""

	# to maintain backwards API compatibility
	updated_title = kwargs.get("new_title") or title
	updated_name = kwargs.get("new_name") or name

	# TODO: omit this after runtime type checking (ref: https://github.com/traquent/traquent/pull/14927)
	for obj in [docname, updated_title, updated_name]:
		if not isinstance(obj, str | NoneType):
			traquent.throw(f"{obj=} must be of type str or None")

	# handle bad API usages
	merge = sbool(merge)
	enqueue = sbool(enqueue)
	action_enqueued = enqueue and not is_scheduler_inactive()

	doc = traquent.get_doc(doctype, docname)
	doc.check_permission(permtype="write")

	title_field = doc.meta.get_title_field()

	title_updated = updated_title and (title_field != "name") and (updated_title != doc.get(title_field))
	name_updated = updated_name and (updated_name != doc.name)

	queue = kwargs.get("queue") or "default"

	if name_updated:
		if action_enqueued:
			current_name = doc.name

			# before_name hook may have DocType specific validations or transformations
			transformed_name = doc.run_method("before_rename", current_name, updated_name, merge)
			if isinstance(transformed_name, dict):
				transformed_name = transformed_name.get("new")
			transformed_name = transformed_name or updated_name

			# run rename validations before queueing
			# use savepoints to avoid partial renames / commits
			validate_rename(
				doctype=doctype,
				old=current_name,
				new=transformed_name,
				meta=doc.meta,
				merge=merge,
				save_point=True,
			)

			doc.queue_action("rename", name=transformed_name, merge=merge, queue=queue)
		else:
			doc.rename(updated_name, merge=merge)

	if title_updated:
		if action_enqueued and name_updated:
			traquent.enqueue(
				"traquent.client.set_value",
				doctype=doc.doctype,
				name=updated_name,
				fieldname=title_field,
				value=updated_title,
			)
		else:
			try:
				setattr(doc, title_field, updated_title)
				doc.save()
				traquent.msgprint(_("Saved"), alert=True, indicator="green")
			except Exception as e:
				if traquent.db.is_duplicate_entry(e):
					traquent.throw(
						_("{0} {1} already exists").format(doctype, traquent.bold(docname)),
						title=_("Duplicate Name"),
						exc=traquent.DuplicateEntryError,
					)
				raise

	return doc.name


def rename_doc(
	doctype: str | None = None,
	old: str | None = None,
	new: str | None = None,
	force: bool = False,
	merge: bool = False,
	ignore_permissions: bool = False,
	ignore_if_exists: bool = False,
	show_alert: bool = True,
	rebuild_search: bool = True,
	doc: Document | None = None,
	validate: bool = True,
) -> str:
	"""Rename a doc(dt, old) to doc(dt, new) and update all linked fields of type "Link".

	doc: Document object to be renamed.
	new: New name for the record. If None, and doctype is specified, new name may be automatically generated via before_rename hooks.
	doctype: DocType of the document. Not required if doc is passed.
	old: Current name of the document. Not required if doc is passed.
	force: Allow even if document is not allowed to be renamed.
	merge: Merge with existing document of new name.
	ignore_permissions: Ignore user permissions while renaming.
	ignore_if_exists: Don't raise exception if document with new name already exists. This will quietely overwrite the existing document.
	show_alert: Display alert if document is renamed successfully.
	rebuild_search: Rebuild linked doctype search after renaming.
	validate: Validate before renaming. If False, it is assumed that the caller has already validated.
	"""
	old_usage_style = doctype and old and new
	new_usage_style = doc and new

	if not (new_usage_style or old_usage_style):
		raise TypeError(
			"{doctype, old, new} or {doc, new} are required arguments for traquent.model.rename_doc"
		)

	old = old or doc.name
	doctype = doctype or doc.doctype
	force = sbool(force)
	merge = sbool(merge)
	meta = traquent.get_meta(doctype)

	if validate:
		old_doc = doc or traquent.get_doc(doctype, old)
		out = old_doc.run_method("before_rename", old, new, merge) or {}
		new = (out.get("new") or new) if isinstance(out, dict) else (out or new)
		new = validate_rename(
			doctype=doctype,
			old=old,
			new=new,
			meta=meta,
			merge=merge,
			force=force,
			ignore_permissions=ignore_permissions,
			ignore_if_exists=ignore_if_exists,
			old_doc=old_doc,
		)

	if not merge:
		rename_parent_and_child(doctype, old, new, meta)
	else:
		update_assignments(old, new, doctype)

	# update link fields' values
	link_fields = get_link_fields(doctype)
	update_link_field_values(link_fields, old, new, doctype)

	rename_dynamic_links(doctype, old, new)

	# save the user settings in the db
	update_user_settings(old, new, link_fields)

	if doctype == "DocType":
		rename_doctype(doctype, old, new)
		update_customizations(old, new)

	update_attachments(doctype, old, new)

	rename_versions(doctype, old, new)

	rename_eps_records(doctype, old, new)

	# call after_rename
	new_doc = traquent.get_doc(doctype, new)

	if validate:
		# copy any flags if required
		new_doc._local = getattr(old_doc, "_local", None)

	new_doc.run_method("after_rename", old, new, merge)

	if not merge:
		rename_password(doctype, old, new)

	if merge:
		new_doc.add_comment("Edit", _("merged {0} into {1}").format(traquent.bold(old), traquent.bold(new)))
	else:
		new_doc.add_comment("Edit", _("renamed from {0} to {1}").format(traquent.bold(old), traquent.bold(new)))

	if merge:
		traquent.delete_doc(doctype, old)

	new_doc.clear_cache()
	traquent.clear_cache()
	if rebuild_search:
		traquent.enqueue("traquent.utils.global_search.rebuild_for_doctype", doctype=doctype)

	if show_alert:
		traquent.msgprint(
			_("Document renamed from {0} to {1}").format(bold(old), bold(new)),
			alert=True,
			indicator="green",
		)

	# let people watching the old form know that it has been renamed
	traquent.publish_realtime(
		event="doc_rename",
		message={"doctype": doctype, "old": old, "new": new},
		doctype=doctype,
		docname=old,
		after_commit=True,
	)

	return new


def update_assignments(old: str, new: str, doctype: str) -> None:
	old_assignments = traquent.parse_json(traquent.db.get_value(doctype, old, "_assign")) or []
	new_assignments = traquent.parse_json(traquent.db.get_value(doctype, new, "_assign")) or []
	common_assignments = list(set(old_assignments).intersection(new_assignments))

	for user in common_assignments:
		# delete todos linked to old doc
		todos = traquent.get_all(
			"ToDo",
			{
				"owner": user,
				"reference_type": doctype,
				"reference_name": old,
			},
			["name", "description"],
		)

		for todo in todos:
			traquent.delete_doc("ToDo", todo.name)

	unique_assignments = list(set(old_assignments + new_assignments))
	traquent.db.set_value(doctype, new, "_assign", traquent.as_json(unique_assignments, indent=0))


def update_user_settings(old: str, new: str, link_fields: list[dict]) -> None:
	"""
	Update the user settings of all the linked doctypes while renaming.
	"""

	# store the user settings data from the redis to db
	sync_user_settings()

	if not link_fields:
		return

	# find the user settings for the linked doctypes
	linked_doctypes = {d.parent for d in link_fields if not d.issingle}
	UserSettings = traquent.qb.Table("__UserSettings")

	user_settings_details = (
		traquent.qb.from_(UserSettings)
		.select("user", "doctype", "data")
		.where(UserSettings.data.like(old) & UserSettings.doctype.isin(linked_doctypes))
		.run(as_dict=True)
	)

	# create the dict using the doctype name as key and values as list of the user settings
	from collections import defaultdict

	user_settings_dict = defaultdict(list)
	for user_setting in user_settings_details:
		user_settings_dict[user_setting.doctype].append(user_setting)

	# update the name in linked doctype whose user settings exists
	for fields in link_fields:
		user_settings = user_settings_dict.get(fields.parent)
		if user_settings:
			for user_setting in user_settings:
				update_user_settings_data(user_setting, "value", old, new, "docfield", fields.fieldname)
		else:
			continue


def update_customizations(old: str, new: str) -> None:
	traquent.db.set_value("Custom DocPerm", {"parent": old}, "parent", new, update_modified=False)


def update_attachments(doctype: str, old: str, new: str) -> None:
	if doctype != "DocType":
		File = traquent.qb.DocType("File")

		traquent.qb.update(File).set(File.attached_to_name, new).where(
			(File.attached_to_name == old) & (File.attached_to_doctype == doctype)
		).run()


def rename_versions(doctype: str, old: str, new: str) -> None:
	Version = traquent.qb.DocType("Version")

	traquent.qb.update(Version).set(Version.docname, new).where(
		(Version.docname == old) & (Version.ref_doctype == doctype)
	).run()


def rename_eps_records(doctype: str, old: str, new: str) -> None:
	EPL = traquent.qb.DocType("Energy Point Log")

	traquent.qb.update(EPL).set(EPL.reference_name, new).where(
		(EPL.reference_doctype == doctype) & (EPL.reference_name == old)
	).run()


def rename_parent_and_child(doctype: str, old: str, new: str, meta: "Meta") -> None:
	traquent.qb.update(doctype).set("name", new).where(Field("name") == old).run()

	update_autoname_field(doctype, new, meta)
	update_child_docs(old, new, meta)


def update_autoname_field(doctype: str, new: str, meta: "Meta") -> None:
	# update the value of the autoname field on rename of the docname
	if meta.get("autoname"):
		field = meta.get("autoname").split(":")
		if field and field[0] == "field":
			traquent.qb.update(doctype).set(field[1], new).where(Field("name") == new).run()


def validate_rename(
	doctype: str,
	old: str,
	new: str,
	meta: "Meta",
	merge: bool,
	force: bool = False,
	ignore_permissions: bool = False,
	ignore_if_exists: bool = False,
	save_point=False,
	old_doc: Document | None = None,
) -> str:
	# using for update so that it gets locked and someone else cannot edit it while this rename is going on!
	if save_point:
		_SAVE_POINT = f"validate_rename_{traquent.generate_hash(length=8)}"
		traquent.db.savepoint(_SAVE_POINT)

	exists = traquent.qb.from_(doctype).where(Field("name") == new).for_update().select("name").run(pluck=True)
	exists = exists[0] if exists else None

	if not traquent.db.exists(doctype, old):
		traquent.throw(_("Can't rename {0} to {1} because {0} doesn't exist.").format(old, new))

	if old == new:
		traquent.throw(_("No changes made because old and new name are the same.").format(old, new))

	if exists and exists != new:
		# for fixing case, accents
		exists = None

	if merge and not exists:
		traquent.throw(_("{0} {1} does not exist, select a new target to merge").format(doctype, new))

	if not merge and exists and not ignore_if_exists:
		traquent.throw(_("Another {0} with name {1} exists, select another name").format(doctype, new))

	kwargs = {"doctype": doctype, "ptype": "write", "print_logs": False}
	if old_doc:
		kwargs |= {"doc": old_doc}

	if not (ignore_permissions or traquent.permissions.has_permission(**kwargs)):
		traquent.throw(_("You need write permission to rename"))

	if not force and not ignore_permissions and not meta.allow_rename:
		traquent.throw(_("{0} not allowed to be renamed").format(_(doctype)))

	# validate naming like it's done in doc.py
	new = validate_name(doctype, new)

	if save_point:
		traquent.db.rollback(save_point=_SAVE_POINT)

	return new


def rename_doctype(doctype: str, old: str, new: str) -> None:
	# change options for fieldtype Table, Table MultiSelect and Link
	fields_with_options = ("Link", *traquent.model.table_fields)

	for fieldtype in fields_with_options:
		update_options_for_fieldtype(fieldtype, old, new)

	# change parenttype for fieldtype Table
	update_parenttype_values(old, new)


def update_child_docs(old: str, new: str, meta: "Meta") -> None:
	# update "parent"
	for df in meta.get_table_fields():
		(
			traquent.qb.update(df.options)
			.set("parent", new)
			.where((Field("parent") == old) & (Field("parenttype") == meta.name))
		).run()


def update_link_field_values(link_fields: list[dict], old: str, new: str, doctype: str) -> None:
	for field in link_fields:
		if field["issingle"]:
			try:
				single_doc = traquent.get_doc(field["parent"])
				if single_doc.get(field["fieldname"]) == old:
					single_doc.set(field["fieldname"], new)
					# update single docs using ORM rather then query
					# as single docs also sometimes sets defaults!
					single_doc.flags.ignore_mandatory = True
					single_doc.save(ignore_permissions=True)
			except ImportError:
				# fails in patches where the doctype has been renamed
				# or no longer exists
				pass
		else:
			parent = field["parent"]
			docfield = field["fieldname"]

			# Handles the case where one of the link fields belongs to
			# the DocType being renamed.
			# Here this field could have the current DocType as its value too.

			# In this case while updating link field value, the field's parent
			# or the current DocType table name hasn't been renamed yet,
			# so consider it's old name.
			if parent == new and doctype == "DocType":
				parent = old

			traquent.db.set_value(parent, {docfield: old}, docfield, new, update_modified=False)

		# update cached link_fields as per new
		if doctype == "DocType" and field["parent"] == old:
			field["parent"] = new


def get_link_fields(doctype: str) -> list[dict]:
	# get link fields from tabDocField
	if not traquent.flags.link_fields:
		traquent.flags.link_fields = {}

	if doctype not in traquent.flags.link_fields:
		dt = traquent.qb.DocType("DocType")
		df = traquent.qb.DocType("DocField")
		cf = traquent.qb.DocType("Custom Field")
		ps = traquent.qb.DocType("Property Setter")

		standard_fields_query = (
			traquent.qb.from_(df)
			.inner_join(dt)
			.on(df.parent == dt.name)
			.select(df.parent, df.fieldname, dt.issingle.as_("issingle"))
			.where((df.options == doctype) & (df.fieldtype == "Link"))
		)

		if traquent.db.has_column("DocField", "is_virtual"):
			standard_fields_query = standard_fields_query.where(df.is_virtual == 0)

		virtual_doctypes = []
		if traquent.db.has_column("DocType", "is_virtual"):
			virtual_doctypes = traquent.get_all("DocType", {"is_virtual": 1}, pluck="name")
			standard_fields_query = standard_fields_query.where(dt.is_virtual == 0)

		standard_fields = standard_fields_query.run(as_dict=True)

		cf_issingle = traquent.qb.from_(dt).select(dt.issingle).where(dt.name == cf.dt).as_("issingle")
		custom_fields = (
			traquent.qb.from_(cf)
			.select(cf.dt.as_("parent"), cf.fieldname, cf_issingle)
			.where((cf.options == doctype) & (cf.fieldtype == "Link"))
		)
		if virtual_doctypes:
			custom_fields = custom_fields.where(cf.dt.notin(virtual_doctypes))
		custom_fields = custom_fields.run(as_dict=True)

		ps_issingle = traquent.qb.from_(dt).select(dt.issingle).where(dt.name == ps.doc_type).as_("issingle")
		property_setter_fields = (
			traquent.qb.from_(ps)
			.select(ps.doc_type.as_("parent"), ps.field_name.as_("fieldname"), ps_issingle)
			.where((ps.property == "options") & (ps.value == doctype) & (ps.field_name.notnull()))
		)
		if virtual_doctypes:
			property_setter_fields = property_setter_fields.where(ps.doc_type.notin(virtual_doctypes))
		property_setter_fields = property_setter_fields.run(as_dict=True)

		traquent.flags.link_fields[doctype] = standard_fields + custom_fields + property_setter_fields

	return traquent.flags.link_fields[doctype]


def update_options_for_fieldtype(fieldtype: str, old: str, new: str) -> None:
	CustomField = traquent.qb.DocType("Custom Field")
	PropertySetter = traquent.qb.DocType("Property Setter")

	if traquent.conf.developer_mode:
		for name in traquent.get_all("DocField", filters={"options": old}, pluck="parent"):
			if name in (old, new):
				continue

			doctype = traquent.get_doc("DocType", name)
			save = False
			for f in doctype.fields:
				if f.options == old:
					f.options = new
					save = True
			if save:
				doctype.save()

	DocField = traquent.qb.DocType("DocField")
	traquent.qb.update(DocField).set(DocField.options, new).where(
		(DocField.fieldtype == fieldtype) & (DocField.options == old)
	).run()

	traquent.qb.update(CustomField).set(CustomField.options, new).where(
		(CustomField.fieldtype == fieldtype) & (CustomField.options == old)
	).run()

	traquent.qb.update(PropertySetter).set(PropertySetter.value, new).where(
		(PropertySetter.property == "options") & (PropertySetter.value == old)
	).run()


def get_select_fields(old: str, new: str) -> list[dict]:
	"""
	get select type fields where doctype's name is hardcoded as
	new line separated list
	"""
	df = traquent.qb.DocType("DocField")
	dt = traquent.qb.DocType("DocType")
	cf = traquent.qb.DocType("Custom Field")
	ps = traquent.qb.DocType("Property Setter")

	# get link fields from tabDocField
	st_issingle = traquent.qb.from_(dt).select(dt.issingle).where(dt.name == df.parent).as_("issingle")
	standard_fields = (
		traquent.qb.from_(df)
		.select(df.parent, df.fieldname, st_issingle)
		.where(
			(df.parent != new)
			& (df.fieldname != "fieldtype")
			& (df.fieldtype == "Select")
			& (df.options.like(f"%{old}%"))
		)
		.run(as_dict=True)
	)

	# get link fields from tabCustom Field
	cf_issingle = traquent.qb.from_(dt).select(dt.issingle).where(dt.name == cf.dt).as_("issingle")
	custom_select_fields = (
		traquent.qb.from_(cf)
		.select(cf.dt.as_("parent"), cf.fieldname, cf_issingle)
		.where((cf.dt != new) & (cf.fieldtype == "Select") & (cf.options.like(f"%{old}%")))
		.run(as_dict=True)
	)

	# remove fields whose options have been changed using property setter
	ps_issingle = traquent.qb.from_(dt).select(dt.issingle).where(dt.name == ps.doc_type).as_("issingle")
	property_setter_select_fields = (
		traquent.qb.from_(ps)
		.select(ps.doc_type.as_("parent"), ps.field_name.as_("fieldname"), ps_issingle)
		.where(
			(ps.doc_type != new)
			& (ps.property == "options")
			& (ps.field_name.notnull())
			& (ps.value.like(f"%{old}%"))
		)
		.run(as_dict=True)
	)

	return standard_fields + custom_select_fields + property_setter_select_fields


def update_select_field_values(old: str, new: str):
	from traquent.query_builder.functions import Replace

	DocField = traquent.qb.DocType("DocField")
	CustomField = traquent.qb.DocType("Custom Field")
	PropertySetter = traquent.qb.DocType("Property Setter")

	traquent.qb.update(DocField).set(DocField.options, Replace(DocField.options, old, new)).where(
		(DocField.fieldtype == "Select")
		& (DocField.parent != new)
		& (DocField.options.like(f"%\n{old}%") | DocField.options.like(f"%{old}\n%"))
	).run()

	traquent.qb.update(CustomField).set(CustomField.options, Replace(CustomField.options, old, new)).where(
		(CustomField.fieldtype == "Select")
		& (CustomField.dt != new)
		& (CustomField.options.like(f"%\n{old}%") | CustomField.options.like(f"%{old}\n%"))
	).run()

	traquent.qb.update(PropertySetter).set(PropertySetter.value, Replace(PropertySetter.value, old, new)).where(
		(PropertySetter.property == "options")
		& (PropertySetter.field_name.notnull())
		& (PropertySetter.doc_type != new)
		& (PropertySetter.value.like(f"%\n{old}%") | PropertySetter.value.like(f"%{old}\n%"))
	).run()


def update_parenttype_values(old: str, new: str):
	child_doctypes = traquent.get_all(
		"DocField",
		fields=["options", "fieldname"],
		filters={"parent": new, "fieldtype": ["in", traquent.model.table_fields]},
	)

	custom_child_doctypes = traquent.get_all(
		"Custom Field",
		fields=["options", "fieldname"],
		filters={"dt": new, "fieldtype": ["in", traquent.model.table_fields]},
	)

	child_doctypes += custom_child_doctypes
	fields = [d["fieldname"] for d in child_doctypes]

	property_setter_child_doctypes = traquent.get_all(
		"Property Setter",
		filters={"doc_type": new, "property": "options", "field_name": ("in", fields)},
		pluck="value",
	)

	child_doctypes = set(list(d["options"] for d in child_doctypes) + property_setter_child_doctypes)

	for doctype in child_doctypes:
		table = traquent.qb.DocType(doctype)
		traquent.qb.update(table).set(table.parenttype, new).where(table.parenttype == old).run()


def rename_dynamic_links(doctype: str, old: str, new: str):
	Singles = traquent.qb.DocType("Singles")
	for df in get_dynamic_link_map().get(doctype, []):
		# dynamic link in single, just one value to check
		meta = traquent.get_meta(df.parent)
		if meta.is_virtual:
			continue
		if meta.issingle:
			refdoc = traquent.db.get_singles_dict(df.parent)
			if refdoc.get(df.options) == doctype and refdoc.get(df.fieldname) == old:
				traquent.qb.update(Singles).set(Singles.value, new).where(
					(Singles.field == df.fieldname) & (Singles.doctype == df.parent) & (Singles.value == old)
				).run()
		else:
			# because the table hasn't been renamed yet!
			parent = df.parent if df.parent != new else old

			traquent.qb.update(parent).set(df.fieldname, new).where(
				(Field(df.options) == doctype) & (Field(df.fieldname) == old)
			).run()


def bulk_rename(doctype: str, rows: list[list] | None = None, via_console: bool = False) -> list[str] | None:
	"""Bulk rename documents

	:param doctype: DocType to be renamed
	:param rows: list of documents as `((oldname, newname, merge(optional)), ..)`"""
	if not rows:
		traquent.throw(_("Please select a valid csv file with data"))

	if not via_console:
		max_rows = 500
		if len(rows) > max_rows:
			traquent.throw(_("Maximum {0} rows allowed").format(max_rows))

	rename_log = []
	for row in rows:
		# if row has some content
		if len(row) > 1 and row[0] and row[1]:
			merge = len(row) > 2 and (row[2] == "1" or row[2].lower() == "true")
			try:
				if rename_doc(doctype, row[0], row[1], merge=merge, rebuild_search=False):
					msg = _("Successful: {0} to {1}").format(row[0], row[1])
					traquent.db.commit()
				else:
					msg = None
			except Exception as e:
				msg = _("** Failed: {0} to {1}: {2}").format(row[0], row[1], repr(e))
				traquent.db.rollback()

			if msg:
				if via_console:
					print(msg)
				else:
					rename_log.append(msg)

	traquent.enqueue("traquent.utils.global_search.rebuild_for_doctype", doctype=doctype)

	if not via_console:
		return rename_log
