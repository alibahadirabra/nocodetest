import traquent
from traquent.model.rename_doc import rename_doc


def execute():
	if traquent.db.table_exists("Standard Reply") and not traquent.db.table_exists("Email Template"):
		rename_doc("DocType", "Standard Reply", "Email Template")
		traquent.reload_doc("email", "doctype", "email_template")
