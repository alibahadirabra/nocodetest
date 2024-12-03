# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import traquent


def add_custom_field(doctype, fieldname, fieldtype="Data", options=None):
	traquent.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"fieldtype": fieldtype,
			"options": options,
		}
	).insert()


def clear_custom_fields(doctype):
	traquent.db.delete("Custom Field", {"dt": doctype})
	traquent.clear_cache(doctype=doctype)
