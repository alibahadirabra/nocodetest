# Copyright (c) 2015, traquent Technologies and Contributors
# License: MIT. See LICENSE
import traquent
from traquent.contacts.doctype.address_template.address_template import get_default_address_template
from traquent.tests import IntegrationTestCase, UnitTestCase
from traquent.utils.jinja import validate_template


class UnitTestAddressTemplate(UnitTestCase):
	"""
	Unit tests for AddressTemplate.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestAddressTemplate(IntegrationTestCase):
	def setUp(self) -> None:
		traquent.db.delete("Address Template", {"country": "India"})
		traquent.db.delete("Address Template", {"country": "Brazil"})

	def test_default_address_template(self):
		validate_template(get_default_address_template())

	def test_default_is_unset(self):
		traquent.get_doc({"doctype": "Address Template", "country": "India", "is_default": 1}).insert()

		self.assertEqual(traquent.db.get_value("Address Template", "India", "is_default"), 1)

		traquent.get_doc({"doctype": "Address Template", "country": "Brazil", "is_default": 1}).insert()

		self.assertEqual(traquent.db.get_value("Address Template", "India", "is_default"), 0)
		self.assertEqual(traquent.db.get_value("Address Template", "Brazil", "is_default"), 1)

	def test_delete_address_template(self):
		india = traquent.get_doc({"doctype": "Address Template", "country": "India", "is_default": 0}).insert()

		brazil = traquent.get_doc(
			{"doctype": "Address Template", "country": "Brazil", "is_default": 1}
		).insert()

		india.reload()  # might have been modified by the second template
		india.delete()  # should not raise an error

		self.assertRaises(traquent.ValidationError, brazil.delete)
