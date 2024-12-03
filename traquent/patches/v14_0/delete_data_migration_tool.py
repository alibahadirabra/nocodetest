# Copyright (c) 2022, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import traquent


def execute():
	doctypes = traquent.get_all("DocType", {"module": "Data Migration", "custom": 0}, pluck="name")
	for doctype in doctypes:
		traquent.delete_doc("DocType", doctype, ignore_missing=True)

	traquent.delete_doc("Module Def", "Data Migration", ignore_missing=True, force=True)
