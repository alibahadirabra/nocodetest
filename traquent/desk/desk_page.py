# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


@traquent.whitelist()
def get(name):
	"""
	Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = traquent.get_doc("Page", name)
	if page.is_permitted():
		page.load_assets()
		docs = traquent._dict(page.as_dict())
		if getattr(page, "_dynamic_page", None):
			docs["_dynamic_page"] = 1

		return docs
	else:
		traquent.response["403"] = 1
		raise traquent.PermissionError("No read permission for Page %s" % (page.title or name))


@traquent.whitelist(allow_guest=True)
def getpage():
	"""
	Load the page from `traquent.form` and send it via `traquent.response`
	"""
	page = traquent.form_dict.get("name")
	doc = get(page)

	traquent.response.docs.append(doc)
