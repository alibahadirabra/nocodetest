# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and contributors
# License: MIT. See LICENSE

import traquent
from traquent.model.document import Document


class UnhandledEmail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		email_account: DF.Link | None
		message_id: DF.Code | None
		raw: DF.Code | None
		reason: DF.LongText | None
		uid: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=30):
		traquent.db.delete(
			"Unhandled Email",
			{
				"creation": ("<", traquent.utils.add_days(traquent.utils.nowdate(), -1 * days)),
			},
		)
