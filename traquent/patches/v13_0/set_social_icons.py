import traquent


def execute():
	providers = traquent.get_all("Social Login Key")

	for provider in providers:
		doc = traquent.get_doc("Social Login Key", provider)
		doc.set_icon()
		doc.save()
