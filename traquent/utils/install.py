# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import getpass

import traquent
from traquent.geo.doctype.country.country import import_country_and_currency
from traquent.utils import cint
from traquent.utils.password import update_password


def before_install():
	traquent.reload_doc("core", "doctype", "doctype_state")
	traquent.reload_doc("core", "doctype", "docfield")
	traquent.reload_doc("core", "doctype", "docperm")
	traquent.reload_doc("core", "doctype", "doctype_action")
	traquent.reload_doc("core", "doctype", "doctype_link")
	traquent.reload_doc("desk", "doctype", "form_tour_step")
	traquent.reload_doc("desk", "doctype", "form_tour")
	traquent.reload_doc("core", "doctype", "doctype")
	traquent.clear_cache()


def after_install():
	create_user_type()
	install_basic_docs()

	from traquent.core.doctype.file.utils import make_home_folder
	from traquent.core.doctype.language.language import sync_languages

	make_home_folder()
	import_country_and_currency()
	sync_languages()

	# save default print setting
	print_settings = traquent.get_doc("Print Settings")
	print_settings.save()

	# all roles to admin
	traquent.get_doc("User", "Administrator").add_roles(*traquent.get_all("Role", pluck="name"))

	# update admin password
	update_password("Administrator", get_admin_password())

	if not traquent.conf.skip_setup_wizard:
		# only set home_page if the value doesn't exist in the db
		if not traquent.db.get_default("desktop:home_page"):
			traquent.db.set_default("desktop:home_page", "setup-wizard")
			traquent.db.set_single_value("System Settings", "setup_complete", 0)

	# clear test log
	from traquent.tests.utils.generators import _after_install_clear_test_log

	_after_install_clear_test_log()

	add_standard_navbar_items()

	traquent.db.commit()


def create_user_type():
	for user_type in ["System User", "Website User"]:
		if not traquent.db.exists("User Type", user_type):
			traquent.get_doc({"doctype": "User Type", "name": user_type, "is_standard": 1}).insert(
				ignore_permissions=True
			)


def install_basic_docs():
	# core users / roles
	install_docs = [
		{
			"doctype": "User",
			"name": "Administrator",
			"first_name": "Administrator",
			"email": "admin@example.com",
			"enabled": 1,
			"is_admin": 1,
			"roles": [{"role": "Administrator"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{
			"doctype": "User",
			"name": "Guest",
			"first_name": "Guest",
			"email": "guest@example.com",
			"enabled": 1,
			"is_guest": 1,
			"roles": [{"role": "Guest"}],
			"thread_notify": 0,
			"send_me_a_copy": 0,
		},
		{"doctype": "Role", "role_name": "Report Manager"},
		{"doctype": "Role", "role_name": "Translator"},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Pending",
			"icon": "question-sign",
			"style": "",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Approved",
			"icon": "ok-sign",
			"style": "Success",
		},
		{
			"doctype": "Workflow State",
			"workflow_state_name": "Rejected",
			"icon": "remove",
			"style": "Danger",
		},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Approve"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Reject"},
		{"doctype": "Workflow Action Master", "workflow_action_name": "Review"},
		{
			"doctype": "Email Domain",
			"domain_name": "example.com",
			"email_id": "account@example.com",
			"password": "pass",
			"email_server": "imap.example.com",
			"use_imap": 1,
			"smtp_server": "smtp.example.com",
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "notifications@example.com",
			"default_outgoing": 1,
		},
		{
			"doctype": "Email Account",
			"domain": "example.com",
			"email_id": "replies@example.com",
			"default_incoming": 1,
		},
	]

	for d in install_docs:
		try:
			traquent.get_doc(d).insert(ignore_if_duplicate=True)
		except traquent.NameError:
			pass


def get_admin_password():
	return traquent.conf.get("admin_password") or getpass.getpass("Set Administrator password: ")


def before_tests():
	if len(traquent.get_installed_apps()) > 1:
		# don't run before tests if any other app is installed
		return

	traquent.db.truncate("Custom Field")
	traquent.db.truncate("Event")

	traquent.clear_cache()

	# complete setup if missing
	if not cint(traquent.db.get_single_value("System Settings", "setup_complete")):
		complete_setup_wizard()

	traquent.db.set_single_value("Website Settings", "disable_signup", 0)
	traquent.db.commit()
	traquent.clear_cache()


def complete_setup_wizard():
	from traquent.desk.page.setup_wizard.setup_wizard import setup_complete

	setup_complete(
		{
			"language": "English",
			"email": "testfrappe.com",
			"full_name": "Test User",
			"password": "test",
			"country": "United States",
			"timezone": "America/New_York",
			"currency": "USD",
			"enable_telemtry": 1,
		}
	)


def add_standard_navbar_items():
	navbar_settings = traquent.get_single("Navbar Settings")

	# don't add settings/help options if they're already present
	if navbar_settings.settings_dropdown and navbar_settings.help_dropdown:
		return

	navbar_settings.settings_dropdown = []
	navbar_settings.help_dropdown = []

	for item in traquent.get_hooks("standard_navbar_items"):
		navbar_settings.append("settings_dropdown", item)

	for item in traquent.get_hooks("standard_help_items"):
		navbar_settings.append("help_dropdown", item)

	navbar_settings.save()
