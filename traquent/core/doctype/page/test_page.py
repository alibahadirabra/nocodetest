# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os
import unittest
from unittest.mock import patch

import traquent
from traquent.tests import IntegrationTestCase, UnitTestCase


class UnitTestPage(UnitTestCase):
	"""
	Unit tests for Page.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestPage(IntegrationTestCase):
	def test_naming(self):
		self.assertRaises(
			traquent.NameError,
			traquent.get_doc(doctype="Page", page_name="DocType", module="Core").insert,
		)

	@unittest.skipUnless(
		os.access(traquent.get_app_path("traquent"), os.W_OK), "Only run if traquent app paths is writable"
	)
	@patch.dict(traquent.conf, {"developer_mode": 1})
	def test_trashing(self):
		page = traquent.new_doc("Page", page_name=traquent.generate_hash(), module="Core").insert()

		page.delete()
		traquent.db.commit()

		module_path = traquent.get_module_path(page.module)
		dir_path = os.path.join(module_path, "page", traquent.scrub(page.name))

		self.assertFalse(os.path.exists(dir_path))
