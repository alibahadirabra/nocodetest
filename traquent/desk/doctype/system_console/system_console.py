# Copyright (c) 2020, traquent Technologies and contributors
# License: MIT. See LICENSE

import json

import traquent
from traquent.model.document import Document
from traquent.utils.safe_exec import read_sql, safe_exec


class SystemConsole(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		commit: DF.Check
		console: DF.Code | None
		output: DF.Code | None
		show_processlist: DF.Check
		type: DF.Literal["Python", "SQL"]
	# end: auto-generated types

	def run(self):
		traquent.only_for("System Manager")
		try:
			traquent.local.debug_log = []
			if self.type == "Python":
				safe_exec(self.console, script_filename="System Console")
				self.output = "\n".join(traquent.debug_log)
			elif self.type == "SQL":
				self.output = traquent.as_json(read_sql(self.console, as_dict=1))
		except Exception:
			self.commit = False
			self.output = traquent.get_traceback()

		if self.commit:
			traquent.db.commit()
		else:
			traquent.db.rollback()
		traquent.get_doc(
			doctype="Console Log", script=self.console, type=self.type, committed=self.commit
		).insert()
		traquent.db.commit()


@traquent.whitelist()
def execute_code(doc):
	console = traquent.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()


@traquent.whitelist()
def show_processlist():
	traquent.only_for("System Manager")
	return _show_processlist()


def _show_processlist():
	return traquent.db.multisql(
		{
			"postgres": """
			SELECT pid AS "Id",
				query_start AS "Time",
				state AS "State",
				query AS "Info",
				wait_event AS "Progress"
			FROM pg_stat_activity""",
			"mariadb": "show full processlist",
		},
		as_dict=True,
	)
