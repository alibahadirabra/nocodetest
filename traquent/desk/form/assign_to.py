# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

"""assign/unassign to ToDo"""

import json

import traquent
import traquent.share
import traquent.utils
from traquent import _
from traquent.desk.doctype.notification_log.notification_log import (
	enqueue_create_notification,
	get_title,
	get_title_html,
)
from traquent.desk.form.document_follow import follow_document
from traquent.utils import escape_html


class DuplicateToDoError(traquent.ValidationError):
	pass


def get(args=None):
	"""get assigned to"""
	if not args:
		args = traquent.local.form_dict

	return traquent.get_all(
		"ToDo",
		fields=["allocated_to as owner", "name"],
		filters={
			"reference_type": args.get("doctype"),
			"reference_name": args.get("name"),
			"status": ("not in", ("Cancelled", "Closed")),
		},
		limit=5,
	)


@traquent.whitelist()
def add(args=None, *, ignore_permissions=False):
	"""add in someone's to do list
	args = {
	        "assign_to": [],
	        "doctype": ,
	        "name": ,
	        "description": ,
	        "assignment_rule":
	}

	"""
	if not args:
		args = traquent.local.form_dict

	users_with_duplicate_todo = []
	shared_with_users = []

	description = escape_html(
		args.get("description", _("Assignment for {0} {1}").format(args["doctype"], args["name"]))
	)

	for assign_to in traquent.parse_json(args.get("assign_to")):
		filters = {
			"reference_type": args["doctype"],
			"reference_name": args["name"],
			"status": "Open",
			"allocated_to": assign_to,
		}
		if not ignore_permissions:
			traquent.get_doc(args["doctype"], args["name"]).check_permission()

		if traquent.get_all("ToDo", filters=filters):
			users_with_duplicate_todo.append(assign_to)
		else:
			from traquent.utils import nowdate

			d = traquent.get_doc(
				{
					"doctype": "ToDo",
					"allocated_to": assign_to,
					"reference_type": args["doctype"],
					"reference_name": args["name"],
					"description": description,
					"priority": args.get("priority", "Medium"),
					"status": "Open",
					"date": args.get("date", nowdate()),
					"assigned_by": args.get("assigned_by", traquent.session.user),
					"assignment_rule": args.get("assignment_rule"),
				}
			).insert(ignore_permissions=True)

			# set assigned_to if field exists
			if traquent.get_meta(args["doctype"]).get_field("assigned_to"):
				traquent.db.set_value(args["doctype"], args["name"], "assigned_to", assign_to)

			doc = traquent.get_doc(args["doctype"], args["name"])

			# if assignee does not have permissions, share or inform
			if not traquent.has_permission(doc=doc, user=assign_to):
				if traquent.get_system_settings("disable_document_sharing"):
					msg = _("User {0} is not permitted to access this document.").format(
						traquent.bold(assign_to)
					)
					msg += "<br>" + _(
						"As document sharing is disabled, please give them the required permissions before assigning."
					)
					traquent.throw(msg, title=_("Missing Permission"))
				else:
					traquent.share.add(doc.doctype, doc.name, assign_to)
					shared_with_users.append(assign_to)

			# make this document followed by assigned user
			if traquent.get_cached_value("User", assign_to, "follow_assigned_documents"):
				follow_document(args["doctype"], args["name"], assign_to)

			# notify
			notify_assignment(
				d.assigned_by,
				d.allocated_to,
				d.reference_type,
				d.reference_name,
				action="ASSIGN",
				description=description,
			)

	if shared_with_users:
		user_list = format_message_for_assign_to(shared_with_users)
		traquent.msgprint(
			_("Shared with the following Users with Read access:{0}").format(user_list, alert=True)
		)

	if users_with_duplicate_todo:
		user_list = format_message_for_assign_to(users_with_duplicate_todo)
		traquent.msgprint(_("Already in the following Users ToDo list:{0}").format(user_list, alert=True))

	return get(args)


@traquent.whitelist()
def add_multiple(args=None):
	if not args:
		args = traquent.local.form_dict

	docname_list = json.loads(args["name"])

	for docname in docname_list:
		args.update({"name": docname})
		add(args)


def close_all_assignments(doctype, name, ignore_permissions=False):
	assignments = traquent.get_all(
		"ToDo",
		fields=["allocated_to", "name"],
		filters=dict(reference_type=doctype, reference_name=name, status=("!=", "Cancelled")),
	)
	if not assignments:
		return False

	for assign_to in assignments:
		set_status(
			doctype,
			name,
			todo=assign_to.name,
			assign_to=assign_to.allocated_to,
			status="Closed",
			ignore_permissions=ignore_permissions,
		)

	return True


@traquent.whitelist()
def remove(doctype, name, assign_to, ignore_permissions=False):
	return set_status(doctype, name, "", assign_to, status="Cancelled", ignore_permissions=ignore_permissions)


@traquent.whitelist()
def remove_multiple(doctype, names, ignore_permissions=False):
	docname_list = json.loads(names)

	for name in docname_list:
		assignments = get({"doctype": doctype, "name": name})

		if not assignments:
			continue

		for assignment in assignments:
			remove(doctype, name, assignment.get("owner"), ignore_permissions)


@traquent.whitelist()
def close(doctype: str, name: str, assign_to: str, ignore_permissions=False):
	if assign_to != traquent.session.user:
		traquent.throw(_("Only the assignee can complete this to-do."))

	return set_status(doctype, name, "", assign_to, status="Closed", ignore_permissions=ignore_permissions)


def set_status(doctype, name, todo=None, assign_to=None, status="Cancelled", ignore_permissions=False):
	"""remove from todo"""

	if not ignore_permissions:
		traquent.get_doc(doctype, name).check_permission()
	try:
		if not todo:
			todo = traquent.db.get_value(
				"ToDo",
				{
					"reference_type": doctype,
					"reference_name": name,
					"allocated_to": assign_to,
					"status": ("!=", status),
				},
			)
		if todo:
			todo = traquent.get_doc("ToDo", todo)
			todo.status = status
			todo.save(ignore_permissions=True)

			notify_assignment(todo.assigned_by, todo.allocated_to, todo.reference_type, todo.reference_name)
	except traquent.DoesNotExistError:
		pass

	# clear assigned_to if field exists
	if traquent.get_meta(doctype).get_field("assigned_to") and status in ("Cancelled", "Closed"):
		traquent.db.set_value(doctype, name, "assigned_to", None)

	return get({"doctype": doctype, "name": name})


def clear(doctype, name, ignore_permissions=False):
	"""
	Clears assignments, return False if not assigned.
	"""
	assignments = traquent.get_all(
		"ToDo",
		fields=["allocated_to", "name"],
		filters=dict(reference_type=doctype, reference_name=name),
	)
	if not assignments:
		return False

	for assign_to in assignments:
		set_status(
			doctype,
			name,
			todo=assign_to.name,
			assign_to=assign_to.allocated_to,
			status="Cancelled",
			ignore_permissions=ignore_permissions,
		)

	return True


def notify_assignment(assigned_by, allocated_to, doc_type, doc_name, action="CLOSE", description=None):
	"""
	Notify assignee that there is a change in assignment
	"""
	if not (assigned_by and allocated_to and doc_type and doc_name):
		return

	assigned_user = traquent.db.get_value("User", allocated_to, ["language", "enabled"], as_dict=True)

	# return if self assigned or user disabled
	if assigned_by == allocated_to or not assigned_user.enabled:
		return

	# Search for email address in description -- i.e. assignee
	user_name = traquent.get_cached_value("User", traquent.session.user, "full_name")
	title = get_title(doc_type, doc_name)
	description_html = f"<div>{description}</div>" if description else None

	if action == "CLOSE":
		subject = _("Your assignment on {0} {1} has been removed by {2}", lang=assigned_user.language).format(
			traquent.bold(_(doc_type)), get_title_html(title), traquent.bold(user_name)
		)
	else:
		user_name = traquent.bold(user_name)
		document_type = traquent.bold(_(doc_type, lang=assigned_user.language))
		title = get_title_html(title)
		subject = _("{0} assigned a new task {1} {2} to you", lang=assigned_user.language).format(
			user_name, document_type, title
		)

	notification_doc = {
		"type": "Assignment",
		"document_type": doc_type,
		"subject": subject,
		"document_name": doc_name,
		"from_user": traquent.session.user,
		"email_content": description_html,
	}

	enqueue_create_notification(allocated_to, notification_doc)


def format_message_for_assign_to(users):
	return "<br><br>" + "<br>".join(users)
