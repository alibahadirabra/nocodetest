# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.reload_doc("Email", "doctype", "Notification")

	notifications = traquent.get_all("Notification", {"is_standard": 1}, {"name", "channel"})
	for notification in notifications:
		if not notification.channel:
			traquent.db.set_value("Notification", notification.name, "channel", "Email", update_modified=False)
			traquent.db.commit()
