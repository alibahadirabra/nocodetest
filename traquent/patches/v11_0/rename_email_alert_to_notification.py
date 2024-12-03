import traquent
from traquent.model.rename_doc import rename_doc


def execute():
	if traquent.db.table_exists("Email Alert Recipient") and not traquent.db.table_exists(
		"Notification Recipient"
	):
		rename_doc("DocType", "Email Alert Recipient", "Notification Recipient")
		traquent.reload_doc("email", "doctype", "notification_recipient")

	if traquent.db.table_exists("Email Alert") and not traquent.db.table_exists("Notification"):
		rename_doc("DocType", "Email Alert", "Notification")
		traquent.reload_doc("email", "doctype", "notification")
