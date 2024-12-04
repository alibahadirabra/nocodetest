import traquent


def execute():
	if not traquent.db.exists("Desk Page"):
		return

	pages = traquent.get_all(
		"Desk Page", filters={"is_standard": False}, fields=["name", "extends", "for_user"]
	)
	default_icon = {}
	for page in pages:
		if page.extends and page.for_user:
			if not default_icon.get(page.extends):
				default_icon[page.extends] = traquent.db.get_value("Desk Page", page.extends, "icon")

			icon = default_icon.get(page.extends)
			traquent.db.set_value("Desk Page", page.name, "icon", icon)