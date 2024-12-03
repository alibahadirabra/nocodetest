# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.reload_doc("core", "doctype", "system_settings", force=1)
	traquent.db.set_single_value("System Settings", "password_reset_limit", 3)
