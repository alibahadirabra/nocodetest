import traquent


def execute():
	"""
	Remove the doctype "Custom Link" that was used to add Custom Links to the
	Dashboard since this is now managed by Customize Form.
	Update `parent` property to the DocType and delte the doctype
	"""
	traquent.reload_doctype("DocType Link")
	if traquent.db.has_table("Custom Link"):
		for custom_link in traquent.get_all("Custom Link", ["name", "document_type"]):
			traquent.db.sql(
				"update `tabDocType Link` set custom=1, parent=%s where parent=%s",
				(custom_link.document_type, custom_link.name),
			)

		traquent.delete_doc("DocType", "Custom Link")
