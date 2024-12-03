# Copyright (c) 2019, traquent Technologies and contributors
# License: MIT. See LICENSE

import traquent
from traquent.model.document import Document
from traquent.query_builder import Interval
from traquent.query_builder.functions import Now


class ScheduledJobLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		debug_log: DF.Code | None
		details: DF.Code | None
		scheduled_job_type: DF.Link
		status: DF.Literal["Scheduled", "Complete", "Failed"]
	# end: auto-generated types

	@staticmethod
	def clear_old_logs(days=90):
		table = traquent.qb.DocType("Scheduled Job Log")
		traquent.db.delete(table, filters=(table.creation < (Now() - Interval(days=days))))
