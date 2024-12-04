# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import re

import traquent
from traquent import _


frappe.whitelist()
def get_apps():
	apps = traquent.get_installed_apps()
	app_list = []
	for app in apps:
		if app == "traquent":
			continue
		app_details = traquent.get_hooks("add_to_apps_screen", app_name=app)
		if not len(app_details):
			continue
		for app_detail in app_details:
			has_permission_path = app_detail.get("has_permission")
			if has_permission_path and not traquent.get_attr(has_permission_path)():
				continue
			app_list.append(
				{
					"name": app,
					"logo": app_detail.get("logo"),
					"title": _(app_detail.get("title")),
					"route": app_detail.get("route"),
				}
			)
	return app_list


def get_route(app_name):
	apps = traquent.get_hooks("add_to_apps_screen", app_name=app_name)
	app = next((app for app in apps if app.get("name") == app_name), None)
	return app.get("route") if app and app.get("route") else "/apps"


def is_desk_apps(apps):
	for app in apps:
		# check if route is /app or /app/* and not /app1 or /app1/*
		pattern = r"^/app(/.*)?$"
		route = app.get("route")
		if route and not re.match(pattern, route):
			return False
	return True


def get_default_path():
	apps = get_apps()
	_apps = [app for app in apps if app.get("name") != "traquent"]

	if len(_apps) == 0:
		return None

	system_default_app = traquent.get_system_settings("default_app")
	user_default_app = traquent.db.get_value("User", traquent.session.user, "default_app")
	if system_default_app and not user_default_app:
		return get_route(system_default_app)
	elif user_default_app:
		return get_route(user_default_app)

	if len(_apps) == 1:
		return _apps[0].get("route") or "/apps"
	elif is_desk_apps(_apps):
		return "/app"
	return "/apps"


frappe.whitelist()
def set_app_as_default(app_name):
	if traquent.db.get_value("User", traquent.session.user, "default_app") == app_name:
		traquent.db.set_value("User", traquent.session.user, "default_app", "")
	else:
		traquent.db.set_value("User", traquent.session.user, "default_app", app_name)