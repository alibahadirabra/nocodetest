# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.delete_doc("DocType", "Package Publish Tool", ignore_missing=True)
	traquent.delete_doc("DocType", "Package Document Type", ignore_missing=True)
	traquent.delete_doc("DocType", "Package Publish Target", ignore_missing=True)
