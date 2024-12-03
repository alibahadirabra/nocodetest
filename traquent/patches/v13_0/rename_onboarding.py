# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	if traquent.db.exists("DocType", "Onboarding"):
		traquent.rename_doc("DocType", "Onboarding", "Module Onboarding", ignore_if_exists=True)
