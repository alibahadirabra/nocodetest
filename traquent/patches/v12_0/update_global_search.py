import traquent
from traquent.desk.page.setup_wizard.install_fixtures import update_global_search_doctypes


def execute():
	traquent.reload_doc("desk", "doctype", "global_search_doctype")
	traquent.reload_doc("desk", "doctype", "global_search_settings")
	update_global_search_doctypes()
