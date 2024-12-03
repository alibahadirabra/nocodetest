import re

import traquent
from traquent.query_builder import DocType


def execute():
	"""Replace temporarily available Database Aggregate APIs on traquent (develop)

	APIs changed:
	        * traquent.db.max => traquent.qb.max
	        * traquent.db.min => traquent.qb.min
	        * traquent.db.sum => traquent.qb.sum
	        * traquent.db.avg => traquent.qb.avg
	"""
	ServerScript = DocType("Server Script")
	server_scripts = (
		traquent.qb.from_(ServerScript)
		.where(
			ServerScript.script.like("%traquent.db.max(%")
			| ServerScript.script.like("%traquent.db.min(%")
			| ServerScript.script.like("%traquent.db.sum(%")
			| ServerScript.script.like("%traquent.db.avg(%")
		)
		.select("name", "script")
		.run(as_dict=True)
	)

	for server_script in server_scripts:
		name, script = server_script["name"], server_script["script"]

		for agg in ["avg", "max", "min", "sum"]:
			script = re.sub(f"traquent.db.{agg}\\(", f"traquent.qb.{agg}(", script)

		traquent.db.set_value("Server Script", name, "script", script)
