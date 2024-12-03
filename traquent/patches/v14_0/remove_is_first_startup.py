import traquent


def execute():
	singles = traquent.qb.Table("tabSingles")
	traquent.qb.from_(singles).delete().where(
		(singles.doctype == "System Settings") & (singles.field == "is_first_startup")
	).run()
