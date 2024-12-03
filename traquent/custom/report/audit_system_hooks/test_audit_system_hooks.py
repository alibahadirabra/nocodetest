# Copyright (c) 2022, traquent Technologies and contributors
# For license information, please see license.txt


from traquent.custom.report.audit_system_hooks.audit_system_hooks import execute
from traquent.tests import IntegrationTestCase


class TestAuditSystemHooksReport(IntegrationTestCase):
	def test_basic_query(self):
		_, data = execute()
		for row in data:
			if row.get("hook_name") == "app_name":
				self.assertEqual(row.get("hook_values"), "traquent")
				break
		else:
			self.fail("Failed to generate hooks report")
