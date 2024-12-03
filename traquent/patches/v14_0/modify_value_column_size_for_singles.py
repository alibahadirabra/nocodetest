import traquent


def execute():
	if traquent.db.db_type == "mariadb":
		traquent.db.sql_ddl("alter table `tabSingles` modify column `value` longtext")
