import traquent


def execute():
	doctype = "Top Bar Item"
	if not traquent.db.table_exists(doctype) or not traquent.db.has_column(doctype, "target"):
		return

	traquent.reload_doc("website", "doctype", "top_bar_item")
	traquent.db.set_value(doctype, {"target": 'target = "_blank"'}, "open_in_new_tab", 1)
