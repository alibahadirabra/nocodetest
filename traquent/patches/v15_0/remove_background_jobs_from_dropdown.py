import traquent


def execute():
	item = traquent.db.exists("Navbar Item", {"item_label": "Background Jobs"})
	if not item:
		return

	traquent.delete_doc("Navbar Item", item)
