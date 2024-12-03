# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent
from traquent import _


@traquent.whitelist()
def get_all_nodes(doctype, label, parent, tree_method, **filters):
	"""Recursively gets all data from tree nodes"""

	if "cmd" in filters:
		del filters["cmd"]
	filters.pop("data", None)

	tree_method = traquent.get_attr(tree_method)

	traquent.is_whitelisted(tree_method)

	data = tree_method(doctype, parent, **filters)
	out = [dict(parent=label, data=data)]

	if "is_root" in filters:
		del filters["is_root"]
	to_check = [d.get("value") for d in data if d.get("expandable")]

	while to_check:
		parent = to_check.pop()
		data = tree_method(doctype, parent, is_root=False, **filters)
		out.append(dict(parent=parent, data=data))
		for d in data:
			if d.get("expandable"):
				to_check.append(d.get("value"))

	return out


@traquent.whitelist()
def get_children(doctype, parent="", include_disabled=False, **filters):
	if isinstance(include_disabled, str):
		include_disabled = traquent.sbool(include_disabled)
	return _get_children(doctype, parent, include_disabled=include_disabled)


def _get_children(doctype, parent="", ignore_permissions=False, include_disabled=False):
	parent_field = "parent_" + traquent.scrub(doctype)
	filters = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]
	if traquent.db.has_column(doctype, "disabled") and not include_disabled:
		filters.append(["disabled", "=", False])

	meta = traquent.get_meta(doctype)

	return traquent.get_list(
		doctype,
		fields=[
			"name as value",
			"{} as title".format(meta.get("title_field") or "name"),
			"is_group as expandable",
		],
		filters=filters,
		order_by="name",
		ignore_permissions=ignore_permissions,
	)


@traquent.whitelist()
def add_node():
	args = make_tree_args(**traquent.form_dict)
	doc = traquent.get_doc(args)

	doc.save()


def make_tree_args(**kwarg):
	kwarg.pop("cmd", None)

	doctype = kwarg["doctype"]
	parent_field = "parent_" + traquent.scrub(doctype)

	if kwarg["is_root"] == "false":
		kwarg["is_root"] = False
	if kwarg["is_root"] == "true":
		kwarg["is_root"] = True

	parent = kwarg.get("parent") or kwarg.get(parent_field)
	if doctype != parent:
		kwarg.update({parent_field: parent})

	return traquent._dict(kwarg)
