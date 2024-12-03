# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.reload_doc("core", "doctype", "DocField")

	if traquent.db.has_column("DocField", "show_days"):
		traquent.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_days = 1 WHERE show_days = 0
		"""
		)
		traquent.db.sql_ddl("alter table tabDocField drop column show_days")

	if traquent.db.has_column("DocField", "show_seconds"):
		traquent.db.sql(
			"""
			UPDATE
				tabDocField
			SET
				hide_seconds = 1 WHERE show_seconds = 0
		"""
		)
		traquent.db.sql_ddl("alter table tabDocField drop column show_seconds")

	traquent.clear_cache(doctype="DocField")
