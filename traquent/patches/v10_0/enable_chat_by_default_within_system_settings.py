import traquent


def execute():
	traquent.reload_doctype("System Settings")
	doc = traquent.get_single("System Settings")
	doc.enable_chat = 1

	# Changes prescribed by Nabin Hait (nabinfrappe.io)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True

	doc.save()
