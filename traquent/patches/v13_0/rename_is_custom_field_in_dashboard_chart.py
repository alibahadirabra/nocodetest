import traquent
from traquent.model.utils.rename_field import rename_field


def execute():
	if not traquent.db.table_exists("Dashboard Chart"):
		return

	traquent.reload_doc("desk", "doctype", "dashboard_chart")

	if traquent.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
