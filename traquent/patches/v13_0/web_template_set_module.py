# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	"""Set default module for standard Web Template, if none."""
	traquent.reload_doc("website", "doctype", "Web Template Field")
	traquent.reload_doc("website", "doctype", "web_template")

	standard_templates = traquent.get_list("Web Template", {"standard": 1})
	for template in standard_templates:
		doc = traquent.get_doc("Web Template", template.name)
		if not doc.module:
			doc.module = "Website"
			doc.save()
