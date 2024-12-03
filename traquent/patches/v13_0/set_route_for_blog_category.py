import traquent


def execute():
	categories = traquent.get_list("Blog Category")
	for category in categories:
		doc = traquent.get_doc("Blog Category", category["name"])
		doc.set_route()
		doc.save()
