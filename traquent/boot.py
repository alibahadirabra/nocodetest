# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
"""
bootstrap client session
"""

import os

import traquent
import traquent.defaults
import traquent.desk.desk_page
from traquent.core.doctype.navbar_settings.navbar_settings import get_app_logo, get_navbar_settings
from traquent.desk.doctype.changelog_feed.changelog_feed import get_changelog_feed_items
from traquent.desk.doctype.form_tour.form_tour import get_onboarding_ui_tours
from traquent.desk.doctype.route_history.route_history import frequently_visited_links
from traquent.desk.form.load import get_meta_bundle
from traquent.email.inbox import get_email_accounts
from traquent.model.base_document import get_controller
from traquent.permissions import has_permission
from traquent.query_builder import DocType
from traquent.query_builder.functions import Count
from traquent.query_builder.terms import ParameterizedValueWrapper, SubQuery
from traquent.social.doctype.energy_point_log.energy_point_log import get_energy_points
from traquent.social.doctype.energy_point_settings.energy_point_settings import (
	is_energy_point_enabled,
)
from traquent.utils import add_user_info, cstr, get_system_timezone
from traquent.utils.change_log import get_versions
from traquent.utils.traquentcloud import on_traquentcloud
from traquent.website.doctype.web_page_view.web_page_view import is_tracking_enabled


def get_bootinfo():
	"""build and return boot info"""
	from traquent.translate import get_lang_dict, get_translated_doctypes

	traquent.set_user_lang(traquent.session.user)
	bootinfo = traquent._dict()
	hooks = traquent.get_hooks()
	doclist = []

	# user
	get_user(bootinfo)

	# system info
	bootinfo.sitename = traquent.local.site
	bootinfo.sysdefaults = traquent.defaults.get_defaults()
	bootinfo.server_date = traquent.utils.nowdate()

	if traquent.session["user"] != "Guest":
		bootinfo.user_info = get_user_info()

	bootinfo.modules = {}
	bootinfo.module_list = []
	load_desktop_data(bootinfo)
	bootinfo.letter_heads = get_letter_heads()
	bootinfo.active_domains = traquent.get_active_domains()
	bootinfo.all_domains = [d.get("name") for d in traquent.get_all("Domain")]
	add_layouts(bootinfo)

	bootinfo.module_app = traquent.local.module_app
	bootinfo.single_types = [d.name for d in traquent.get_all("DocType", {"issingle": 1})]
	bootinfo.nested_set_doctypes = [
		d.parent for d in traquent.get_all("DocField", {"fieldname": "lft"}, ["parent"])
	]
	add_home_page(bootinfo, doclist)
	bootinfo.page_info = get_allowed_pages()
	load_translations(bootinfo)
	add_timezone_info(bootinfo)
	load_conf_settings(bootinfo)
	load_print(bootinfo, doclist)
	doclist.extend(get_meta_bundle("Page"))
	bootinfo.home_folder = traquent.db.get_value("File", {"is_home_folder": 1})
	bootinfo.navbar_settings = get_navbar_settings()
	bootinfo.notification_settings = get_notification_settings()
	bootinfo.onboarding_tours = get_onboarding_ui_tours()
	set_time_zone(bootinfo)

	# ipinfo
	if traquent.session.data.get("ipinfo"):
		bootinfo.ipinfo = traquent.session["data"]["ipinfo"]

	# add docs
	bootinfo.docs = doclist
	load_country_doc(bootinfo)
	load_currency_docs(bootinfo)

	for method in hooks.boot_session or []:
		traquent.get_attr(method)(bootinfo)

	if bootinfo.lang:
		bootinfo.lang = str(bootinfo.lang)
	bootinfo.versions = {k: v["version"] for k, v in get_versions().items()}

	bootinfo.error_report_email = traquent.conf.error_report_email
	bootinfo.calendars = sorted(traquent.get_hooks("calendars"))
	bootinfo.treeviews = traquent.get_hooks("treeviews") or []
	bootinfo.lang_dict = get_lang_dict()
	bootinfo.success_action = get_success_action()
	bootinfo.update(get_email_accounts(user=traquent.session.user))
	bootinfo.energy_points_enabled = is_energy_point_enabled()
	bootinfo.website_tracking_enabled = is_tracking_enabled()
	bootinfo.points = get_energy_points(traquent.session.user)
	bootinfo.frequently_visited_links = frequently_visited_links()
	bootinfo.link_preview_doctypes = get_link_preview_doctypes()
	bootinfo.additional_filters_config = get_additional_filters_from_hooks()
	bootinfo.desk_settings = get_desk_settings()
	bootinfo.app_logo_url = get_app_logo()
	bootinfo.link_title_doctypes = get_link_title_doctypes()
	bootinfo.translated_doctypes = get_translated_doctypes()
	bootinfo.subscription_conf = add_subscription_conf()
	bootinfo.marketplace_apps = get_marketplace_apps()
	bootinfo.changelog_feed = get_changelog_feed_items()
	bootinfo.enable_address_autocompletion = traquent.db.get_single_value(
		"Geolocation Settings", "enable_address_autocompletion"
	)

	if sentry_dsn := get_sentry_dsn():
		bootinfo.sentry_dsn = sentry_dsn

	return bootinfo


def get_letter_heads():
	letter_heads = {}

	if not traquent.has_permission("Letter Head"):
		return letter_heads
	for letter_head in traquent.get_list("Letter Head", fields=["name", "content", "footer"]):
		letter_heads.setdefault(
			letter_head.name, {"header": letter_head.content, "footer": letter_head.footer}
		)

	return letter_heads


def load_conf_settings(bootinfo):
	from traquent.core.api.file import get_max_file_size

	bootinfo.max_file_size = get_max_file_size()
	for key in ("developer_mode", "socketio_port", "file_watcher_port"):
		if key in traquent.conf:
			bootinfo[key] = traquent.conf.get(key)


def load_desktop_data(bootinfo):
	from traquent.desk.desktop import get_workspace_sidebar_items

	bootinfo.sidebar_pages = get_workspace_sidebar_items()
	allowed_pages = [d.name for d in bootinfo.sidebar_pages.get("pages")]
	bootinfo.module_wise_workspaces = get_controller("Workspace").get_module_wise_workspaces()
	bootinfo.dashboards = traquent.get_all("Dashboard")
	bootinfo.app_data = []

	Workspace = traquent.qb.DocType("Workspace")
	Module = traquent.qb.DocType("Module Def")

	for app_name in traquent.get_installed_apps():
		# get app details from app_info (/apps)
		apps = traquent.get_hooks("add_to_apps_screen", app_name=app_name)
		app_info = {}
		if apps:
			app_info = apps[0]
			has_permission = app_info.get("has_permission")
			if has_permission and not traquent.get_attr(has_permission)():
				continue

		workspaces = [
			r[0]
			for r in (
				traquent.qb.from_(Workspace)
				.inner_join(Module)
				.on(Workspace.module == Module.name)
				.select(Workspace.name)
				.where(Module.app_name == app_name)
				.run()
			)
			if r[0] in allowed_pages
		]

		bootinfo.app_data.append(
			dict(
				app_name=app_info.get("name") or app_name,
				app_title=app_info.get("title")
				or (
					traquent.get_hooks("app_title", app_name=app_name)
					and traquent.get_hooks("app_title", app_name=app_name)[0]
					or ""
				)
				or app_name,
				app_route=(
					traquent.get_hooks("app_home", app_name=app_name)
					and traquent.get_hooks("app_home", app_name=app_name)[0]
				)
				or (workspaces and "/app/" + traquent.utils.slug(workspaces[0]))
				or "",
				app_logo_url=app_info.get("logo")
				or traquent.get_hooks("app_logo_url", app_name=app_name)
				or traquent.get_hooks("app_logo_url", app_name="traquent"),
				modules=[m.name for m in traquent.get_all("Module Def", dict(app_name=app_name))],
				workspaces=workspaces,
			)
		)


def get_allowed_pages(cache=False):
	return get_user_pages_or_reports("Page", cache=cache)


def get_allowed_reports(cache=False):
	return get_user_pages_or_reports("Report", cache=cache)


def get_allowed_report_names(cache=False) -> set[str]:
	return {cstr(report) for report in get_allowed_reports(cache).keys() if report}


def get_user_pages_or_reports(parent, cache=False):
	if cache:
		has_role = traquent.cache.get_value("has_role:" + parent, user=traquent.session.user)
		if has_role:
			return has_role

	roles = traquent.get_roles()
	has_role = {}

	page = DocType("Page")
	report = DocType("Report")

	is_report = parent == "Report"

	if is_report:
		columns = (report.name.as_("title"), report.ref_doctype, report.report_type)
	else:
		columns = (page.title.as_("title"),)

	customRole = DocType("Custom Role")
	hasRole = DocType("Has Role")
	parentTable = DocType(parent)

	# get pages or reports set on custom role
	pages_with_custom_roles = (
		traquent.qb.from_(customRole)
		.from_(hasRole)
		.from_(parentTable)
		.select(customRole[parent.lower()].as_("name"), customRole.modified, customRole.ref_doctype, *columns)
		.where(
			(hasRole.parent == customRole.name)
			& (parentTable.name == customRole[parent.lower()])
			& (customRole[parent.lower()].isnotnull())
			& (hasRole.role.isin(roles))
		)
	).run(as_dict=True)

	for p in pages_with_custom_roles:
		has_role[p.name] = {"modified": p.modified, "title": p.title, "ref_doctype": p.ref_doctype}

	subq = (
		traquent.qb.from_(customRole)
		.select(customRole[parent.lower()])
		.where(customRole[parent.lower()].isnotnull())
	)

	pages_with_standard_roles = (
		traquent.qb.from_(hasRole)
		.from_(parentTable)
		.select(parentTable.name.as_("name"), parentTable.modified, *columns)
		.where(
			(hasRole.role.isin(roles)) & (hasRole.parent == parentTable.name) & (parentTable.name.notin(subq))
		)
		.distinct()
	)

	if is_report:
		pages_with_standard_roles = pages_with_standard_roles.where(report.disabled == 0)

	pages_with_standard_roles = pages_with_standard_roles.run(as_dict=True)

	for p in pages_with_standard_roles:
		if p.name not in has_role:
			has_role[p.name] = {"modified": p.modified, "title": p.title}
			if parent == "Report":
				has_role[p.name].update({"ref_doctype": p.ref_doctype})

	no_of_roles = SubQuery(
		traquent.qb.from_(hasRole).select(Count("*")).where(hasRole.parent == parentTable.name)
	)

	# pages and reports with no role are allowed
	rows_with_no_roles = (
		traquent.qb.from_(parentTable)
		.select(parentTable.name, parentTable.modified, *columns)
		.where(no_of_roles == 0)
	).run(as_dict=True)

	for r in rows_with_no_roles:
		if r.name not in has_role:
			has_role[r.name] = {"modified": r.modified, "title": r.title}
			if is_report:
				has_role[r.name] |= {"ref_doctype": r.ref_doctype}

	if is_report:
		if not has_permission("Report", print_logs=False):
			return {}

		reports = traquent.get_list(
			"Report",
			fields=["name", "report_type"],
			filters={"name": ("in", has_role.keys())},
			ignore_ifnull=True,
		)
		for report in reports:
			has_role[report.name]["report_type"] = report.report_type

		non_permitted_reports = set(has_role.keys()) - {r.name for r in reports}
		for r in non_permitted_reports:
			has_role.pop(r, None)

	# Expire every six hours
	traquent.cache.set_value("has_role:" + parent, has_role, traquent.session.user, 21600)
	return has_role


def load_translations(bootinfo):
	from traquent.translate import get_messages_for_boot

	bootinfo["lang"] = traquent.lang
	bootinfo["__messages"] = get_messages_for_boot()


def get_user_info():
	# get info for current user
	user_info = traquent._dict()
	add_user_info(traquent.session.user, user_info)

	return user_info


def get_user(bootinfo):
	"""get user info"""
	bootinfo.user = traquent.get_user().load_user()


def add_home_page(bootinfo, docs):
	"""load home page"""
	if traquent.session.user == "Guest":
		return
	home_page = traquent.db.get_default("desktop:home_page")

	if home_page == "setup-wizard":
		bootinfo.setup_wizard_requires = traquent.get_hooks("setup_wizard_requires")

	try:
		page = traquent.desk.desk_page.get(home_page)
		docs.append(page)
		bootinfo["home_page"] = page.name
	except (traquent.DoesNotExistError, traquent.PermissionError):
		traquent.clear_last_message()
		bootinfo["home_page"] = "Workspaces"


def add_timezone_info(bootinfo):
	system = bootinfo.sysdefaults.get("time_zone")
	import traquent.utils.momentjs

	bootinfo.timezone_info = {"zones": {}, "rules": {}, "links": {}}
	traquent.utils.momentjs.update(system, bootinfo.timezone_info)


def load_print(bootinfo, doclist):
	print_settings = traquent.db.get_singles_dict("Print Settings")
	print_settings.doctype = ":Print Settings"
	doclist.append(print_settings)
	load_print_css(bootinfo, print_settings)


def load_print_css(bootinfo, print_settings):
	import traquent.www.printview

	bootinfo.print_css = traquent.www.printview.get_print_style(
		print_settings.print_style or "Redesign", for_legacy=True
	)


def get_unseen_notes():
	note = DocType("Note")
	nsb = DocType("Note Seen By").as_("nsb")

	return (
		traquent.qb.from_(note)
		.select(note.name, note.title, note.content, note.notify_on_every_login)
		.where(
			(note.notify_on_login == 1)
			& (note.expire_notification_on > traquent.utils.now())
			& (
				ParameterizedValueWrapper(traquent.session.user).notin(
					SubQuery(traquent.qb.from_(nsb).select(nsb.user).where(nsb.parent == note.name))
				)
			)
		)
	).run(as_dict=1)


def get_success_action():
	return traquent.get_all("Success Action", fields=["*"])


def get_link_preview_doctypes():
	from traquent.utils import cint

	link_preview_doctypes = [d.name for d in traquent.get_all("DocType", {"show_preview_popup": 1})]
	customizations = traquent.get_all(
		"Property Setter", fields=["doc_type", "value"], filters={"property": "show_preview_popup"}
	)

	for custom in customizations:
		if not cint(custom.value) and custom.doc_type in link_preview_doctypes:
			link_preview_doctypes.remove(custom.doc_type)
		else:
			link_preview_doctypes.append(custom.doc_type)

	return link_preview_doctypes


def get_additional_filters_from_hooks():
	filter_config = traquent._dict()
	filter_hooks = traquent.get_hooks("filters_config")
	for hook in filter_hooks:
		filter_config.update(traquent.get_attr(hook)())

	return filter_config


def add_layouts(bootinfo):
	# add routes for readable doctypes
	bootinfo.doctype_layouts = traquent.get_all("DocType Layout", ["name", "route", "document_type"])


def get_desk_settings():
	from traquent.core.doctype.user.user import desk_properties

	return traquent.get_value("User", traquent.session.user, desk_properties, as_dict=True)


def get_notification_settings():
	return traquent.get_cached_doc("Notification Settings", traquent.session.user)


def get_link_title_doctypes():
	dts = traquent.get_all("DocType", {"show_title_field_in_link": 1})
	custom_dts = traquent.get_all(
		"Property Setter",
		{"property": "show_title_field_in_link", "value": "1"},
		["doc_type as name"],
	)
	return [d.name for d in dts + custom_dts if d]


def set_time_zone(bootinfo):
	bootinfo.time_zone = {
		"system": get_system_timezone(),
		"user": bootinfo.get("user_info", {}).get(traquent.session.user, {}).get("time_zone", None)
		or get_system_timezone(),
	}


def load_country_doc(bootinfo):
	country = traquent.db.get_default("country")
	if not country:
		return
	try:
		bootinfo.docs.append(traquent.get_cached_doc("Country", country))
	except Exception:
		pass


def load_currency_docs(bootinfo):
	currency = traquent.qb.DocType("Currency")

	currency_docs = (
		traquent.qb.from_(currency)
		.select(
			currency.name,
			currency.fraction,
			currency.fraction_units,
			currency.number_format,
			currency.smallest_currency_fraction_value,
			currency.symbol,
			currency.symbol_on_right,
		)
		.where(currency.enabled == 1)
		.run(as_dict=1, update={"doctype": ":Currency"})
	)

	bootinfo.docs += currency_docs


def get_marketplace_apps():
	import requests

	apps = []
	cache_key = "traquent_marketplace_apps"

	if traquent.conf.developer_mode or not on_traquentcloud():
		return apps

	def get_apps_from_fc():
		remote_site = traquent.conf.traquentcloud_url or "traquentcloud.com"
		request_url = f"https://{remote_site}/api/method/press.api.marketplace.get_marketplace_apps"
		request = requests.get(request_url, timeout=2.0)
		return request.json()["message"]

	try:
		apps = traquent.cache.get_value(cache_key, get_apps_from_fc, shared=True)
		installed_apps = set(traquent.get_installed_apps())
		apps = [app for app in apps if app["name"] not in installed_apps]
	except Exception:
		# Don't retry for a day
		traquent.cache.set_value(cache_key, apps, shared=True, expires_in_sec=24 * 60 * 60)

	return apps


def add_subscription_conf():
	try:
		return traquent.conf.subscription
	except Exception:
		return ""


def get_sentry_dsn():
	if not traquent.get_system_settings("enable_telemetry"):
		return

	return os.getenv("traquent_SENTRY_DSN")