# Copyright (c) 2020, traquent Technologies and contributors
# License: MIT. See LICENSE

import json

import traquent

# import traquent
from traquent.model.document import Document


class DashboardSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		chart_config: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types

	pass


frappe.whitelist()
def create_dashboard_settings(user):
	if not traquent.db.exists("Dashboard Settings", user):
		doc = traquent.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		traquent.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = traquent.session.user

	return f"""(`tabDashboard Settings`.name = {traquent.db.escape(user)})"""


frappe.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = traquent.parse_json(reset)
	doc = traquent.get_doc("Dashboard Settings", traquent.session.user)
	chart_config = traquent.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = traquent.parse_json(config)
		if chart_name not in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	traquent.db.set_value("Dashboard Settings", traquent.session.user, "chart_config", json.dumps(chart_config))
