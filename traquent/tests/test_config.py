# Copyright (c) 2022, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import traquent
from traquent.tests import IntegrationTestCase
from traquent.utils.modules import get_modules_from_all_apps_for_user


class TestConfig(IntegrationTestCase):
	def test_get_modules(self):
		traquent_modules = traquent.get_all("Module Def", filters={"app_name": "traquent"}, pluck="name")
		all_modules_data = get_modules_from_all_apps_for_user()
		all_modules = [x["module_name"] for x in all_modules_data]
		self.assertIsInstance(all_modules_data, list)
		self.assertFalse([x for x in traquent_modules if x not in all_modules])
