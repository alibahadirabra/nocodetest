import traquent
from traquent.desk.doctype.notification_settings.notification_settings import (
	create_notification_settings,
)


def execute():
	traquent.reload_doc("desk", "doctype", "notification_settings")
	traquent.reload_doc("desk", "doctype", "notification_subscribed_document")

	users = traquent.get_all("User", fields=["name"])
	for user in users:
		create_notification_settings(user.name)
