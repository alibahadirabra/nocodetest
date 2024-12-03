import traquent


def execute():
	traquent.reload_doctype("Letter Head")

	# source of all existing letter heads must be HTML
	traquent.db.sql("update `tabLetter Head` set source = 'HTML'")
