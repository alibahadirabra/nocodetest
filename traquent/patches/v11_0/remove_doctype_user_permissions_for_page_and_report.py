# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.delete_doc_if_exists("DocType", "User Permission for Page and Report")
