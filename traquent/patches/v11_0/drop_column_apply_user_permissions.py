import traquent


def execute():
	column = "apply_user_permissions"
	to_remove = ["DocPerm", "Custom DocPerm"]

	for doctype in to_remove:
		if traquent.db.table_exists(doctype):
			if column in traquent.db.get_table_columns(doctype):
				traquent.db.sql(f"alter table `tab{doctype}` drop column {column}")

	traquent.reload_doc("core", "doctype", "docperm", force=True)
	traquent.reload_doc("core", "doctype", "custom_docperm", force=True)
