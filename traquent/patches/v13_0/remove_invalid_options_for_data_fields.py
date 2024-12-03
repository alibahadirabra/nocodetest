# Copyright (c) 2022, traquent and Contributors
# License: MIT. See LICENSE


import traquent
from traquent.model import data_field_options


def execute():
	custom_field = traquent.qb.DocType("Custom Field")
	(
		traquent.qb.update(custom_field)
		.set(custom_field.options, None)
		.where((custom_field.fieldtype == "Data") & (custom_field.options.notin(data_field_options)))
	).run()
