import traquent


def execute():
	traquent.reload_doc("core", "doctype", "doctype_link")
	traquent.reload_doc("core", "doctype", "doctype_action")
	traquent.reload_doc("core", "doctype", "doctype")
	traquent.model.delete_fields({"DocType": ["hide_heading", "image_view", "read_only_onload"]}, delete=1)

	traquent.db.delete("Property Setter", {"property": "read_only_onload"})
