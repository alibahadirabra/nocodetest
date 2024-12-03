# Copyright (c) 2018, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent


def execute():
	traquent.db.set_value("Currency", "USD", "smallest_currency_fraction_value", "0.01")
