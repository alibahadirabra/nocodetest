# Copyright (c) 2021, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import traquent


def execute():
	traquent.reload_doc("website", "doctype", "web_form_list_column")
	traquent.reload_doctype("Web Form")

	for web_form in traquent.get_all("Web Form", fields=["*"]):
		if web_form.allow_multiple and not web_form.show_list:
			traquent.db.set_value("Web Form", web_form.name, "show_list", True)
