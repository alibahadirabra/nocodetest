import traquent
from traquent.utils.install import add_standard_navbar_items


def execute():
	# Add standard navbar items for ERPNext in Navbar Settings
	traquent.reload_doc("core", "doctype", "navbar_settings")
	traquent.reload_doc("core", "doctype", "navbar_item")
	add_standard_navbar_items()
