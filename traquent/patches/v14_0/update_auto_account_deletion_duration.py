import traquent


def execute():
	days = traquent.db.get_single_value("Website Settings", "auto_account_deletion")
	traquent.db.set_single_value("Website Settings", "auto_account_deletion", days * 24)
