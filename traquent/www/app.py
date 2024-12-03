# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import os

no_cache = 1

import json
import re
from urllib.parse import urlencode

import traquent
import traquent.sessions
from traquent import _
from traquent.utils.jinja_globals import is_rtl

SCRIPT_TAG_PATTERN = re.compile(r"\<script[^<]*\</script\>")
CLOSING_SCRIPT_TAG_PATTERN = re.compile(r"</script\>")


def get_context(context):
	if traquent.session.user == "Guest":
		traquent.response["status_code"] = 403
		traquent.msgprint(_("Log in to access this page."))
		traquent.redirect(f"/login?{urlencode({'redirect-to': traquent.request.path})}")

	elif traquent.db.get_value("User", traquent.session.user, "user_type", order_by=None) == "Website User":
		traquent.throw(_("You are not permitted to access this page."), traquent.PermissionError)

	try:
		boot = traquent.sessions.get()
	except Exception as e:
		raise traquent.SessionBootFailed from e

	# this needs commit
	csrf_token = traquent.sessions.get_csrf_token()

	traquent.db.commit()

	boot_json = traquent.as_json(boot, indent=None, separators=(",", ":"))

	# remove script tags from boot
	boot_json = SCRIPT_TAG_PATTERN.sub("", boot_json)

	# TODO: Find better fix
	boot_json = CLOSING_SCRIPT_TAG_PATTERN.sub("", boot_json)
	boot_json = json.dumps(boot_json)

	hooks = traquent.get_hooks()
	app_include_js = hooks.get("app_include_js", []) + traquent.conf.get("app_include_js", [])
	app_include_css = hooks.get("app_include_css", []) + traquent.conf.get("app_include_css", [])
	app_include_icons = hooks.get("app_include_icons", [])

	if traquent.get_system_settings("enable_telemetry") and os.getenv("traquent_SENTRY_DSN"):
		app_include_js.append("sentry.bundle.js")

	context.update(
		{
			"no_cache": 1,
			"build_version": traquent.utils.get_build_version(),
			"app_include_js": app_include_js,
			"app_include_css": app_include_css,
			"app_include_icons": app_include_icons,
			"layout_direction": "rtl" if is_rtl() else "ltr",
			"lang": traquent.local.lang,
			"sounds": hooks["sounds"],
			"boot": boot if context.get("for_mobile") else boot_json,
			"desk_theme": boot.get("desk_theme") or "Light",
			"csrf_token": csrf_token,
			"google_analytics_id": traquent.conf.get("google_analytics_id"),
			"google_analytics_anonymize_ip": traquent.conf.get("google_analytics_anonymize_ip"),
			"app_name": (
				traquent.get_website_settings("app_name") or traquent.get_system_settings("app_name") or "traquent"
			),
		}
	)

	return context
