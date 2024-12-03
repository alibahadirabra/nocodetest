# Copyright (c) 2018, traquent Technologies and contributors
# License: MIT. See LICENSE

import traquent
from traquent.model.document import Document


class ViewLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
		viewed_by: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=180):
		from traquent.query_builder import Interval
		from traquent.query_builder.functions import Now

		table = traquent.qb.DocType("View Log")
		traquent.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))
