import traquent
from traquent.utils.install import create_user_type


def execute():
	traquent.reload_doc("core", "doctype", "role")
	traquent.reload_doc("core", "doctype", "user_document_type")
	traquent.reload_doc("core", "doctype", "user_type_module")
	traquent.reload_doc("core", "doctype", "user_select_document_type")
	traquent.reload_doc("core", "doctype", "user_type")

	create_user_type()
