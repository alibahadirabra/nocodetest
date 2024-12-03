# Copyright (c) 2020, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	"""Enable all the existing Client script"""

	traquent.db.sql(
		"""
		UPDATE `tabClient Script` SET enabled=1
	"""
	)
