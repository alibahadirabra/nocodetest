# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	if not traquent.db.table_exists("Data Import"):
		return

	meta = traquent.get_meta("Data Import")
	# if Data Import is the new one, return early
	if meta.fields[1].fieldname == "import_type":
		return

	traquent.db.sql("DROP TABLE IF EXISTS `tabData Import Legacy`")
	traquent.rename_doc("DocType", "Data Import", "Data Import Legacy")
	traquent.db.commit()
	traquent.db.sql("DROP TABLE IF EXISTS `tabData Import`")
	traquent.rename_doc("DocType", "Data Import Beta", "Data Import")
