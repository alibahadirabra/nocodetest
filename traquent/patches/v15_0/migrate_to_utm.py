import traquent


def execute():
	"""
	Rename the Marketing Campaign table to UTM Campaign table
	"""
	if traquent.db.exists("DocType", "UTM Campaign"):
		return
	traquent.rename_doc("DocType", "Marketing Campaign", "UTM Campaign", force=True)
	traquent.reload_doctype("UTM Campaign", force=True)
