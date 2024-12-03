# Copyright (c) 2015, traquent Technologies and Contributors
# License: MIT. See LICENSE
import time

import traquent
from traquent.auth import CookieManager, LoginManager
from traquent.tests import IntegrationTestCase, UnitTestCase


class UnitTestActivityLog(UnitTestCase):
	"""
	Unit tests for ActivityLog.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestActivityLog(IntegrationTestCase):
	def setUp(self) -> None:
		traquent.set_user("Administrator")

	def test_activity_log(self):
		# test user login log
		traquent.local.form_dict = traquent._dict(
			{
				"cmd": "login",
				"sid": "Guest",
				"pwd": self.ADMIN_PASSWORD or "admin",
				"usr": "Administrator",
			}
		)

		traquent.local.request_ip = "127.0.0.1"
		traquent.local.cookie_manager = CookieManager()
		traquent.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertFalse(traquent.form_dict.pwd)
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		traquent.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		traquent.form_dict.update({"pwd": "password"})
		self.assertRaises(traquent.AuthenticationError, LoginManager)
		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Failed")

		traquent.local.form_dict = traquent._dict()

	def get_auth_log(self, operation="Login"):
		names = traquent.get_all(
			"Activity Log",
			filters={
				"user": "Administrator",
				"operation": operation,
			},
			order_by="`creation` DESC",
		)

		name = names[0]
		return traquent.get_doc("Activity Log", name)

	def test_brute_security(self):
		update_system_settings({"allow_consecutive_login_attempts": 3, "allow_login_after_fail": 5})

		traquent.local.form_dict = traquent._dict(
			{"cmd": "login", "sid": "Guest", "pwd": self.ADMIN_PASSWORD, "usr": "Administrator"}
		)

		traquent.local.request_ip = "127.0.0.1"
		traquent.local.cookie_manager = CookieManager()
		traquent.local.login_manager = LoginManager()

		auth_log = self.get_auth_log()
		self.assertEqual(auth_log.status, "Success")

		# test user logout log
		traquent.local.login_manager.logout()
		auth_log = self.get_auth_log(operation="Logout")
		self.assertEqual(auth_log.status, "Success")

		# test invalid login
		traquent.form_dict.update({"pwd": "password"})
		self.assertRaises(traquent.AuthenticationError, LoginManager)
		self.assertRaises(traquent.AuthenticationError, LoginManager)
		self.assertRaises(traquent.AuthenticationError, LoginManager)

		# REMOVE ME: current logic allows allow_consecutive_login_attempts+1 attempts
		# before raising security exception, remove below line when that is fixed.
		self.assertRaises(traquent.AuthenticationError, LoginManager)
		self.assertRaises(traquent.SecurityException, LoginManager)
		time.sleep(5)
		self.assertRaises(traquent.AuthenticationError, LoginManager)

		traquent.local.form_dict = traquent._dict()


def update_system_settings(args):
	doc = traquent.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
