import json

import traquent


def execute():
	if traquent.db.exists("Social Login Key", "github"):
		traquent.db.set_value(
			"Social Login Key", "github", "auth_url_data", json.dumps({"scope": "user:email"})
		)
