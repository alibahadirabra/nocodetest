import traquent


def execute():
	traquent.db.delete("DocType", {"name": "Feedback Request"})
