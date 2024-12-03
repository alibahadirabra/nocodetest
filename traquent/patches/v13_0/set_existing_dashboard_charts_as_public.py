import traquent


def execute():
	traquent.reload_doc("desk", "doctype", "dashboard_chart")

	if not traquent.db.table_exists("Dashboard Chart"):
		return

	users_with_permission = traquent.get_all(
		"Has Role",
		fields=["parent"],
		filters={"role": ["in", ["System Manager", "Dashboard Manager"]], "parenttype": "User"},
		distinct=True,
	)

	users = [item.parent for item in users_with_permission]
	charts = traquent.get_all("Dashboard Chart", filters={"owner": ["in", users]})

	for chart in charts:
		traquent.db.set_value("Dashboard Chart", chart.name, "is_public", 1)
