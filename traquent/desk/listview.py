# Copyright (c) 2022, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent
from traquent.model import is_default_field
from traquent.query_builder import Order
from traquent.query_builder.functions import Count
from traquent.query_builder.terms import SubQuery
from traquent.query_builder.utils import DocType


@traquent.whitelist()
def get_list_settings(doctype):
	try:
		return traquent.get_cached_doc("List View Settings", doctype)
	except traquent.DoesNotExistError:
		traquent.clear_messages()


@traquent.whitelist()
def set_list_settings(doctype, values):
	try:
		doc = traquent.get_doc("List View Settings", doctype)
	except traquent.DoesNotExistError:
		doc = traquent.new_doc("List View Settings")
		doc.name = doctype
		traquent.clear_messages()
	doc.update(traquent.parse_json(values))
	doc.save()


@traquent.whitelist()
def get_group_by_count(doctype: str, current_filters: str, field: str) -> list[dict]:
	current_filters = traquent.parse_json(current_filters)

	if field == "assigned_to":
		ToDo = DocType("ToDo")
		User = DocType("User")
		count = Count("*").as_("count")
		filtered_records = traquent.qb.get_query(
			doctype,
			filters=current_filters,
			fields=["name"],
			validate_filters=True,
		)

		return (
			traquent.qb.from_(ToDo)
			.from_(User)
			.select(ToDo.allocated_to.as_("name"), count)
			.where(
				(ToDo.status != "Cancelled")
				& (ToDo.allocated_to == User.name)
				& (User.user_type == "System User")
				& (ToDo.reference_name.isin(SubQuery(filtered_records)))
			)
			.groupby(ToDo.allocated_to)
			.orderby(count, order=Order.desc)
			.limit(50)
			.run(as_dict=True)
		)

	meta = traquent.get_meta(doctype)

	if not meta.has_field(field) and not is_default_field(field):
		raise ValueError("Field does not belong to doctype")

	data = traquent.get_list(
		doctype,
		filters=current_filters,
		group_by=f"`tab{doctype}`.{field}",
		fields=["count(*) as count", f"`{field}` as name"],
		order_by="count desc",
		limit=50,
	)

	# Add in title if it's a link field and `show_title_field_in_link` is set
	if (field_meta := meta.get_field(field)) and field_meta.fieldtype == "Link":
		link_meta = traquent.get_meta(field_meta.options)
		if link_meta.show_title_field_in_link:
			title_field = link_meta.get_title_field()
			for item in data:
				item.title = traquent.get_value(field_meta.options, item.name, title_field)

	return data
