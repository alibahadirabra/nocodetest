import traquent


def execute():
	if traquent.db.table_exists("Prepared Report"):
		traquent.reload_doc("core", "doctype", "prepared_report")
		prepared_reports = traquent.get_all("Prepared Report")
		for report in prepared_reports:
			traquent.delete_doc("Prepared Report", report.name)
