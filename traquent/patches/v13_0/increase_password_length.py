import traquent


def execute():
	traquent.db.change_column_type("__Auth", column="password", type="TEXT")
