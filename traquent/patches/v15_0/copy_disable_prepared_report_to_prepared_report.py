import traquent


def execute():
	table = traquent.qb.DocType("Report")
	traquent.qb.update(table).set(table.prepared_report, 0).where(table.disable_prepared_report == 1)
