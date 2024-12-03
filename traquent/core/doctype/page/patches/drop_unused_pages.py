import traquent


def execute():
	for name in ("desktop", "space"):
		traquent.delete_doc("Page", name)
