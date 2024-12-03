import json

import traquent


def execute():
	"""Handle introduction of UI tours"""
	completed = {}
	for tour in traquent.get_all("Form Tour", {"ui_tour": 1}, pluck="name"):
		completed[tour] = {"is_complete": True}

	User = traquent.qb.DocType("User")
	traquent.qb.update(User).set("onboarding_status", json.dumps(completed)).run()
