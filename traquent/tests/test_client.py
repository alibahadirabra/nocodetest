# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors

from unittest.mock import patch

import traquent
from traquent.tests import IntegrationTestCase
from traquent.utils import get_site_url


class TestClient(IntegrationTestCase):
	def test_set_value(self):
		todo = traquent.get_doc(doctype="ToDo", description="test").insert()
		traquent.set_value("ToDo", todo.name, "description", "test 1")
		self.assertEqual(traquent.get_value("ToDo", todo.name, "description"), "test 1")

		traquent.set_value("ToDo", todo.name, {"description": "test 2"})
		self.assertEqual(traquent.get_value("ToDo", todo.name, "description"), "test 2")

	def test_delete(self):
		from traquent.client import delete
		from traquent.desk.doctype.note.note import Note

		note = traquent.get_doc(
			doctype="Note",
			title=traquent.generate_hash(length=8),
			content="test",
			seen_by=[{"user": "Administrator"}],
		).insert()

		child_row_name = note.seen_by[0].name

		with patch.object(Note, "save") as save:
			delete("Note Seen By", child_row_name)
			save.assert_called()

		delete("Note", note.name)

		self.assertFalse(traquent.db.exists("Note", note.name))
		self.assertRaises(traquent.DoesNotExistError, delete, "Note", note.name)
		self.assertRaises(traquent.DoesNotExistError, delete, "Note Seen By", child_row_name)

	def test_http_valid_method_access(self):
		from traquent.client import delete
		from traquent.handler import execute_cmd

		traquent.set_user("Administrator")

		traquent.local.request = traquent._dict()
		traquent.local.request.method = "POST"

		traquent.local.form_dict = traquent._dict(
			{"doc": dict(doctype="ToDo", description="Valid http method"), "cmd": "traquent.client.save"}
		)
		todo = execute_cmd("traquent.client.save")

		self.assertEqual(todo.get("description"), "Valid http method")

		delete("ToDo", todo.name)

	def test_http_invalid_method_access(self):
		from traquent.handler import execute_cmd

		traquent.set_user("Administrator")

		traquent.local.request = traquent._dict()
		traquent.local.request.method = "GET"

		traquent.local.form_dict = traquent._dict(
			{"doc": dict(doctype="ToDo", description="Invalid http method"), "cmd": "traquent.client.save"}
		)

		self.assertRaises(traquent.PermissionError, execute_cmd, "traquent.client.save")

	def test_run_doc_method(self):
		from traquent.handler import execute_cmd

		if not traquent.db.exists("Report", "Test Run Doc Method"):
			report = traquent.get_doc(
				{
					"doctype": "Report",
					"ref_doctype": "User",
					"report_name": "Test Run Doc Method",
					"report_type": "Query Report",
					"is_standard": "No",
					"roles": [{"role": "System Manager"}],
				}
			).insert()
		else:
			report = traquent.get_doc("Report", "Test Run Doc Method")

		traquent.local.request = traquent._dict()
		traquent.local.request.method = "GET"

		# Whitelisted, works as expected
		traquent.local.form_dict = traquent._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "toggle_disable",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		execute_cmd(traquent.local.form_dict.cmd)

		# Not whitelisted, throws permission error
		traquent.local.form_dict = traquent._dict(
			{
				"dt": report.doctype,
				"dn": report.name,
				"method": "create_report_py",
				"cmd": "run_doc_method",
				"args": 0,
			}
		)

		self.assertRaises(traquent.PermissionError, execute_cmd, traquent.local.form_dict.cmd)

	def test_array_values_in_request_args(self):
		import requests

		from traquent.auth import CookieManager, LoginManager

		traquent.utils.set_request(path="/")
		traquent.local.cookie_manager = CookieManager()
		traquent.local.login_manager = LoginManager()
		traquent.local.login_manager.login_as("Administrator")
		params = {
			"doctype": "DocType",
			"fields": ["name", "modified"],
			"sid": traquent.session.sid,
		}
		headers = {
			"accept": "application/json",
			"content-type": "application/json",
		}
		url = get_site_url(traquent.local.site)
		url += "/api/method/traquent.client.get_list"

		res = requests.post(url, json=params, headers=headers)
		self.assertEqual(res.status_code, 200)
		data = res.json()
		first_item = data["message"][0]
		self.assertTrue("name" in first_item)
		self.assertTrue("modified" in first_item)

	def test_client_get(self):
		from traquent.client import get

		todo = traquent.get_doc(doctype="ToDo", description="test").insert()
		filters = {"name": todo.name}
		filters_json = traquent.as_json(filters)

		self.assertEqual(get("ToDo", filters=filters).description, "test")
		self.assertEqual(get("ToDo", filters=filters_json).description, "test")
		self.assertEqual(get("System Settings", "", "").doctype, "System Settings")
		self.assertEqual(get("ToDo", filters={}), get("ToDo", filters="{}"))
		todo.delete()

	def test_client_insert(self):
		from traquent.client import insert

		def get_random_title():
			return f"test-{traquent.generate_hash()}"

		# test insert dict
		doc = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(doc)
		self.assertTrue(note1)

		# test insert json
		doc["title"] = get_random_title()
		json_doc = traquent.as_json(doc)
		note2 = insert(json_doc)
		self.assertTrue(note2)

		# test insert child doc without parent fields
		child_doc = {"doctype": "Note Seen By", "user": "Administrator"}
		with self.assertRaises(traquent.ValidationError):
			insert(child_doc)

		# test insert child doc with parent fields
		child_doc = {
			"doctype": "Note Seen By",
			"user": "Administrator",
			"parenttype": "Note",
			"parent": note1.name,
			"parentfield": "seen_by",
		}
		note3 = insert(child_doc)
		self.assertTrue(note3)

		# cleanup
		traquent.delete_doc("Note", note1.name)
		traquent.delete_doc("Note", note2.name)

	def test_client_insert_many(self):
		from traquent.client import insert, insert_many

		def get_random_title():
			return f"test-{traquent.generate_hash(length=5)}"

		# insert a (parent) doc
		note1 = {"doctype": "Note", "title": get_random_title(), "content": "test"}
		note1 = insert(note1)

		doc_list = [
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{
				"doctype": "Note Seen By",
				"user": "Administrator",
				"parenttype": "Note",
				"parent": note1.name,
				"parentfield": "seen_by",
			},
			{"doctype": "Note", "title": "not-a-random-title", "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": get_random_title(), "content": "test"},
			{"doctype": "Note", "title": "another-note-title", "content": "test"},
		]

		# insert all docs
		docs = insert_many(doc_list)

		self.assertEqual(len(docs), 7)
		self.assertEqual(traquent.db.get_value("Note", docs[3], "title"), "not-a-random-title")
		self.assertEqual(traquent.db.get_value("Note", docs[6], "title"), "another-note-title")
		self.assertIn(note1.name, docs)

		# cleanup
		for doc in docs:
			traquent.delete_doc("Note", doc)
