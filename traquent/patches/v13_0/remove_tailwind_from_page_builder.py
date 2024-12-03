# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.reload_doc("website", "doctype", "web_page_block")
	# remove unused templates
	traquent.delete_doc("Web Template", "Navbar with Links on Right", force=1)
	traquent.delete_doc("Web Template", "Footer Horizontal", force=1)
