# Copyright (c) 2018, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	signatures = traquent.db.get_list("User", {"email_signature": ["!=", ""]}, ["name", "email_signature"])
	traquent.reload_doc("core", "doctype", "user")
	for d in signatures:
		signature = d.get("email_signature")
		signature = signature.replace("\n", "<br>")
		signature = "<div>" + signature + "</div>"
		traquent.db.set_value("User", d.get("name"), "email_signature", signature)
