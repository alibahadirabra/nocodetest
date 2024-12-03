# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import traquent
from traquent.cache_manager import clear_controller_cache
from traquent.desk.doctype.todo.todo import ToDo
from traquent.tests import IntegrationTestCase
from traquent.tests.test_api import traquentAPITestCase


class TestHooks(IntegrationTestCase):
	def test_hooks(self):
		hooks = traquent.get_hooks()
		self.assertTrue(isinstance(hooks.get("app_name"), list))
		self.assertTrue(isinstance(hooks.get("doc_events"), dict))
		self.assertTrue(isinstance(hooks.get("doc_events").get("*"), dict))
		self.assertTrue(isinstance(hooks.get("doc_events").get("*"), dict))
		self.assertTrue(
			"traquent.desk.notifications.clear_doctype_notifications"
			in hooks.get("doc_events").get("*").get("on_update")
		)

	def test_override_doctype_class(self):
		from traquent import hooks

		# Set hook
		hooks.override_doctype_class = {"ToDo": ["traquent.tests.test_hooks.CustomToDo"]}

		# Clear cache
		traquent.cache.delete_value("app_hooks")
		clear_controller_cache("ToDo")

		todo = traquent.get_doc(doctype="ToDo", description="asdf")
		self.assertTrue(isinstance(todo, CustomToDo))

	def test_has_permission(self):
		from traquent import hooks

		# Set hook
		address_has_permission_hook = hooks.has_permission.get("Address", [])
		if isinstance(address_has_permission_hook, str):
			address_has_permission_hook = [address_has_permission_hook]

		address_has_permission_hook.append("traquent.tests.test_hooks.custom_has_permission")

		hooks.has_permission["Address"] = address_has_permission_hook

		wildcard_has_permission_hook = hooks.has_permission.get("*", [])
		if isinstance(wildcard_has_permission_hook, str):
			wildcard_has_permission_hook = [wildcard_has_permission_hook]

		wildcard_has_permission_hook.append("traquent.tests.test_hooks.custom_has_permission")

		hooks.has_permission["*"] = wildcard_has_permission_hook

		# Clear cache
		traquent.cache.delete_value("app_hooks")

		# Init User and Address
		username = "test@example.com"
		user = traquent.get_doc("User", username)
		user.add_roles("System Manager")
		address = traquent.new_doc("Address")

		# Create Note
		note = traquent.new_doc("Note")
		note.public = 1

		# Test!
		self.assertTrue(traquent.has_permission("Address", doc=address, user=username))
		self.assertTrue(traquent.has_permission("Note", doc=note, user=username))

		address.flags.dont_touch_me = True
		self.assertFalse(traquent.has_permission("Address", doc=address, user=username))

		note.flags.dont_touch_me = True
		self.assertFalse(traquent.has_permission("Note", doc=note, user=username))

	def test_ignore_links_on_delete(self):
		email_unsubscribe = traquent.get_doc(
			{"doctype": "Email Unsubscribe", "email": "test@example.com", "global_unsubscribe": 1}
		).insert()

		event = traquent.get_doc(
			{
				"doctype": "Event",
				"subject": "Test Event",
				"starts_on": "2022-12-21",
				"event_type": "Public",
				"event_participants": [
					{
						"reference_doctype": "Email Unsubscribe",
						"reference_docname": email_unsubscribe.name,
					}
				],
			}
		).insert()
		self.assertRaises(traquent.LinkExistsError, email_unsubscribe.delete)

		event.event_participants = []
		event.save()

		todo = traquent.get_doc(
			{
				"doctype": "ToDo",
				"description": "Test ToDo",
				"reference_type": "Event",
				"reference_name": event.name,
			}
		)
		todo.insert()

		event.delete()

	def test_fixture_prefix(self):
		import os
		import shutil

		from traquent import hooks
		from traquent.utils.fixtures import export_fixtures

		app = "traquent"
		if os.path.isdir(traquent.get_app_path(app, "fixtures")):
			shutil.rmtree(traquent.get_app_path(app, "fixtures"))

		# use any set of core doctypes for test purposes
		hooks.fixtures = [
			{"dt": "User"},
			{"dt": "Contact"},
			{"dt": "Role"},
		]
		hooks.fixture_auto_order = False
		# every call to traquent.get_hooks loads the hooks module into cache
		# therefor the cache has to be invalidated after every manual overwriting of hooks
		# TODO replace with a more elegant solution if there is one or build a util function for this purpose
		if traquent._load_app_hooks.__wrapped__ in traquent.local.request_cache.keys():
			del traquent.local.request_cache[traquent._load_app_hooks.__wrapped__]
		self.assertEqual([False], traquent.get_hooks("fixture_auto_order", app_name=app))
		self.assertEqual(
			[
				{"dt": "User"},
				{"dt": "Contact"},
				{"dt": "Role"},
			],
			traquent.get_hooks("fixtures", app_name=app),
		)

		export_fixtures(app)
		# use assertCountEqual (replaced assertItemsEqual), beacuse os.listdir might return the list in a different order, depending on OS
		self.assertCountEqual(
			["user.json", "contact.json", "role.json"], os.listdir(traquent.get_app_path(app, "fixtures"))
		)

		hooks.fixture_auto_order = True
		del traquent.local.request_cache[traquent._load_app_hooks.__wrapped__]
		self.assertEqual([True], traquent.get_hooks("fixture_auto_order", app_name=app))

		shutil.rmtree(traquent.get_app_path(app, "fixtures"))
		export_fixtures(app)
		self.assertCountEqual(
			["1_user.json", "2_contact.json", "3_role.json"],
			os.listdir(traquent.get_app_path(app, "fixtures")),
		)

		hooks.fixtures = [
			{"dt": "User", "prefix": "my_prefix"},
			{"dt": "Contact"},
			{"dt": "Role"},
		]
		hooks.fixture_auto_order = False

		del traquent.local.request_cache[traquent._load_app_hooks.__wrapped__]
		shutil.rmtree(traquent.get_app_path(app, "fixtures"))
		export_fixtures(app)
		self.assertCountEqual(
			["my_prefix_user.json", "contact.json", "role.json"],
			os.listdir(traquent.get_app_path(app, "fixtures")),
		)

		hooks.fixture_auto_order = True
		del traquent.local.request_cache[traquent._load_app_hooks.__wrapped__]
		shutil.rmtree(traquent.get_app_path(app, "fixtures"))
		export_fixtures(app)
		self.assertCountEqual(
			["1_my_prefix_user.json", "2_contact.json", "3_role.json"],
			os.listdir(traquent.get_app_path(app, "fixtures")),
		)


class TestAPIHooks(traquentAPITestCase):
	def test_auth_hook(self):
		with self.patch_hooks({"auth_hooks": ["traquent.tests.test_hooks.custom_auth"]}):
			site_url = traquent.utils.get_site_url(traquent.local.site)
			response = self.get(
				site_url + "/api/method/traquent.auth.get_logged_user",
				headers={"Authorization": "Bearer set_test_example_user"},
			)
			# Test!
			self.assertTrue(response.json.get("message") == "test@example.com")


def custom_has_permission(doc, ptype, user):
	if doc.flags.dont_touch_me:
		return False
	return True


def custom_auth():
	auth_type, token = traquent.get_request_header("Authorization", "Bearer ").split(" ")
	if token == "set_test_example_user":
		traquent.set_user("test@example.com")


class CustomToDo(ToDo):
	pass
