# Copyright (c) 2018, traquent Technologies and Contributors
# License: MIT. See LICENSE
import hashlib

import traquent
from traquent.tests import IntegrationTestCase, UnitTestCase


class UnitTestTransactionLog(UnitTestCase):
	"""
	Unit tests for TransactionLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestTransactionLog(IntegrationTestCase):
	def test_validate_chaining(self):
		traquent.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 1",
				"data": "first_data",
			}
		).insert(ignore_permissions=True)

		second_log = traquent.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 2",
				"data": "second_data",
			}
		).insert(ignore_permissions=True)

		third_log = traquent.get_doc(
			{
				"doctype": "Transaction Log",
				"reference_doctype": "Test Doctype",
				"document_name": "Test Document 3",
				"data": "third_data",
			}
		).insert(ignore_permissions=True)

		sha = hashlib.sha256()
		sha.update(
			traquent.safe_encode(str(third_log.transaction_hash))
			+ traquent.safe_encode(str(second_log.chaining_hash))
		)

		self.assertEqual(sha.hexdigest(), third_log.chaining_hash)
