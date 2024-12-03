# Copyright (c) 2024, traquent Technologies and Contributors
# See license.txt

import traquent
from traquent.tests import IntegrationTestCase, UnitTestCase


class UnitTestSystemHealthReport(UnitTestCase):
	"""
	Unit tests for SystemHealthReport.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestSystemHealthReport(IntegrationTestCase):
	def test_it_works(self):
		traquent.get_doc("System Health Report")
