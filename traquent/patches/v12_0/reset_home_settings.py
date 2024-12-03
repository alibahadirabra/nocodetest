import traquent


def execute():
	traquent.reload_doc("core", "doctype", "user")
	traquent.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
