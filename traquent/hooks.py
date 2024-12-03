import os

from . import __version__ as app_version

app_name = "traquent"
app_title = "Creinda"
app_publisher = "traquent Technologies"
app_description = "Full stack web framework with Python, Javascript, MariaDB, Redis, Node"
app_license = "MIT"
app_logo_url = "/assets/traquent/images/traquent-framework-logo.svg"
develop_version = "15.x.x-develop"
app_home = "/app/build"

app_email = "developers@traquent.io"

before_install = "traquent.utils.install.before_install"
after_install = "traquent.utils.install.after_install"

page_js = {"setup-wizard": "public/js/traquent/setup_wizard.js"}

# website
app_include_js = [
	"libs.bundle.js",
	"desk.bundle.js",
	"list.bundle.js",
	"form.bundle.js",
	"controls.bundle.js",
	"report.bundle.js",
	"telemetry.bundle.js",
]

app_include_css = [
	"desk.bundle.css",
	"report.bundle.css",
]
app_include_icons = [
	"/assets/traquent/icons/timeless/icons.svg",
	"/assets/traquent/icons/espresso/icons.svg",
]

doctype_js = {
	"Web Page": "public/js/traquent/utils/web_template.js",
	"Website Settings": "public/js/traquent/utils/web_template.js",
}

web_include_js = ["website_script.js"]
web_include_css = []
web_include_icons = [
	"/assets/traquent/icons/timeless/icons.svg",
	"/assets/traquent/icons/espresso/icons.svg",
]

email_css = ["email.bundle.css"]

website_route_rules = [
	{"from_route": "/blog/<category>", "to_route": "Blog Post"},
	{"from_route": "/kb/<category>", "to_route": "Help Article"},
	{"from_route": "/newsletters", "to_route": "Newsletter"},
	{"from_route": "/profile", "to_route": "me"},
	{"from_route": "/app/<path:app_path>", "to_route": "app"},
]

website_redirects = [
	{"source": r"/desk(.*)", "target": r"/app\1"},
	{
		"source": "/.well-known/openid-configuration",
		"target": "/api/method/traquent.integrations.oauth2.openid_configuration",
	},
]

base_template = "templates/base.html"

write_file_keys = ["file_url", "file_name"]

notification_config = "traquent.core.notifications.get_notification_config"

before_tests = "traquent.utils.install.before_tests"

email_append_to = ["Event", "ToDo", "Communication"]

calendars = ["Event"]

leaderboards = "traquent.desk.leaderboard.get_leaderboards"

# login

on_session_creation = [
	"traquent.core.doctype.activity_log.feed.login_feed",
	"traquent.core.doctype.user.user.notify_admin_access_to_system_manager",
]

on_logout = "traquent.core.doctype.session_default_settings.session_default_settings.clear_session_defaults"

# PDF
pdf_header_html = "traquent.utils.pdf.pdf_header_html"
pdf_body_html = "traquent.utils.pdf.pdf_body_html"
pdf_footer_html = "traquent.utils.pdf.pdf_footer_html"

# permissions

permission_query_conditions = {
	"Event": "traquent.desk.doctype.event.event.get_permission_query_conditions",
	"ToDo": "traquent.desk.doctype.todo.todo.get_permission_query_conditions",
	"User": "traquent.core.doctype.user.user.get_permission_query_conditions",
	"Dashboard Settings": "traquent.desk.doctype.dashboard_settings.dashboard_settings.get_permission_query_conditions",
	"Notification Log": "traquent.desk.doctype.notification_log.notification_log.get_permission_query_conditions",
	"Dashboard": "traquent.desk.doctype.dashboard.dashboard.get_permission_query_conditions",
	"Dashboard Chart": "traquent.desk.doctype.dashboard_chart.dashboard_chart.get_permission_query_conditions",
	"Number Card": "traquent.desk.doctype.number_card.number_card.get_permission_query_conditions",
	"Notification Settings": "traquent.desk.doctype.notification_settings.notification_settings.get_permission_query_conditions",
	"Note": "traquent.desk.doctype.note.note.get_permission_query_conditions",
	"Kanban Board": "traquent.desk.doctype.kanban_board.kanban_board.get_permission_query_conditions",
	"Contact": "traquent.contacts.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "traquent.contacts.address_and_contact.get_permission_query_conditions_for_address",
	"Communication": "traquent.core.doctype.communication.communication.get_permission_query_conditions_for_communication",
	"Workflow Action": "traquent.workflow.doctype.workflow_action.workflow_action.get_permission_query_conditions",
	"Prepared Report": "traquent.core.doctype.prepared_report.prepared_report.get_permission_query_condition",
	"File": "traquent.core.doctype.file.file.get_permission_query_conditions",
}

has_permission = {
	"Event": "traquent.desk.doctype.event.event.has_permission",
	"ToDo": "traquent.desk.doctype.todo.todo.has_permission",
	"Note": "traquent.desk.doctype.note.note.has_permission",
	"User": "traquent.core.doctype.user.user.has_permission",
	"Dashboard Chart": "traquent.desk.doctype.dashboard_chart.dashboard_chart.has_permission",
	"Number Card": "traquent.desk.doctype.number_card.number_card.has_permission",
	"Kanban Board": "traquent.desk.doctype.kanban_board.kanban_board.has_permission",
	"Contact": "traquent.contacts.address_and_contact.has_permission",
	"Address": "traquent.contacts.address_and_contact.has_permission",
	"Communication": "traquent.core.doctype.communication.communication.has_permission",
	"Workflow Action": "traquent.workflow.doctype.workflow_action.workflow_action.has_permission",
	"File": "traquent.core.doctype.file.file.has_permission",
	"Prepared Report": "traquent.core.doctype.prepared_report.prepared_report.has_permission",
	"Notification Settings": "traquent.desk.doctype.notification_settings.notification_settings.has_permission",
}

has_website_permission = {"Address": "traquent.contacts.doctype.address.address.has_website_permission"}

jinja = {
	"methods": "traquent.utils.jinja_globals",
	"filters": [
		"traquent.utils.data.global_date_format",
		"traquent.utils.markdown",
		"traquent.website.utils.abs_url",
	],
}

standard_queries = {"User": "traquent.core.doctype.user.user.user_query"}

doc_events = {
	"*": {
		"on_update": [
			"traquent.desk.notifications.clear_doctype_notifications",
			"traquent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"traquent.core.doctype.file.utils.attach_files_to_document",
			"traquent.automation.doctype.assignment_rule.assignment_rule.apply",
			"traquent.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"traquent.core.doctype.user_type.user_type.apply_permissions_for_non_standard_user_type",
			"traquent.core.doctype.permission_log.permission_log.make_perm_log",
		],
		"after_rename": "traquent.desk.notifications.clear_doctype_notifications",
		"on_cancel": [
			"traquent.desk.notifications.clear_doctype_notifications",
			"traquent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"traquent.automation.doctype.assignment_rule.assignment_rule.apply",
		],
		"on_trash": [
			"traquent.desk.notifications.clear_doctype_notifications",
			"traquent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
		],
		"on_update_after_submit": [
			"traquent.workflow.doctype.workflow_action.workflow_action.process_workflow_actions",
			"traquent.automation.doctype.assignment_rule.assignment_rule.apply",
			"traquent.automation.doctype.assignment_rule.assignment_rule.update_due_date",
			"traquent.core.doctype.file.utils.attach_files_to_document",
		],
		"on_change": [
			"traquent.social.doctype.energy_point_rule.energy_point_rule.process_energy_points",
			"traquent.automation.doctype.milestone_tracker.milestone_tracker.evaluate_milestone",
		],
		"after_delete": ["traquent.core.doctype.permission_log.permission_log.make_perm_log"],
	},
	"Event": {
		"after_insert": "traquent.integrations.doctype.google_calendar.google_calendar.insert_event_in_google_calendar",
		"on_update": "traquent.integrations.doctype.google_calendar.google_calendar.update_event_in_google_calendar",
		"on_trash": "traquent.integrations.doctype.google_calendar.google_calendar.delete_event_from_google_calendar",
	},
	"Contact": {
		"after_insert": "traquent.integrations.doctype.google_contacts.google_contacts.insert_contacts_to_google_contacts",
		"on_update": "traquent.integrations.doctype.google_contacts.google_contacts.update_contacts_to_google_contacts",
	},
	"DocType": {
		"on_update": "traquent.cache_manager.build_domain_restriced_doctype_cache",
	},
	"Page": {
		"on_update": "traquent.cache_manager.build_domain_restriced_page_cache",
	},
}

scheduler_events = {
	"cron": {
		# 5 minutes
		"0/5 * * * *": [
			"traquent.email.doctype.notification.notification.trigger_offset_alerts",
		],
		# 15 minutes
		"0/15 * * * *": [
			"traquent.oauth.delete_oauth2_data",
			"traquent.website.doctype.web_page.web_page.check_publish_status",
			"traquent.twofactor.delete_all_barcodes_for_users",
			"traquent.email.doctype.email_account.email_account.notify_unreplied",
			"traquent.utils.global_search.sync_global_search",
			"traquent.deferred_insert.save_to_db",
		],
		# 10 minutes
		"0/10 * * * *": [
			"traquent.email.doctype.email_account.email_account.pull",
		],
		# Hourly but offset by 30 minutes
		"30 * * * *": [
			"traquent.core.doctype.prepared_report.prepared_report.expire_stalled_report",
		],
		# Daily but offset by 45 minutes
		"45 0 * * *": [
			"traquent.core.doctype.log_settings.log_settings.run_log_clean_up",
		],
	},
	"all": [
		"traquent.email.queue.flush",
		"traquent.monitor.flush",
		"traquent.automation.doctype.reminder.reminder.send_reminders",
	],
	"hourly": [
		"traquent.model.utils.link_count.update_link_count",
		"traquent.model.utils.user_settings.sync_user_settings",
		"traquent.desk.page.backups.backups.delete_downloadable_backups",
		"traquent.desk.form.document_follow.send_hourly_updates",
		"traquent.integrations.doctype.google_calendar.google_calendar.sync",
		"traquent.email.doctype.newsletter.newsletter.send_scheduled_email",
		"traquent.website.doctype.personal_data_deletion_request.personal_data_deletion_request.process_data_deletion_request",
	],
	"daily": [
		"traquent.desk.notifications.clear_notifications",
		"traquent.desk.doctype.event.event.send_event_digest",
		"traquent.sessions.clear_expired_sessions",
		"traquent.email.doctype.notification.notification.trigger_daily_alerts",
		"traquent.website.doctype.personal_data_deletion_request.personal_data_deletion_request.remove_unverified_record",
		"traquent.desk.form.document_follow.send_daily_updates",
		"traquent.social.doctype.energy_point_settings.energy_point_settings.allocate_review_points",
		"traquent.integrations.doctype.google_contacts.google_contacts.sync",
		"traquent.automation.doctype.auto_repeat.auto_repeat.make_auto_repeat_entry",
		"traquent.automation.doctype.auto_repeat.auto_repeat.set_auto_repeat_as_completed",
	],
	"daily_long": [
		"traquent.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_daily",
		"traquent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_daily",
		"traquent.email.doctype.auto_email_report.auto_email_report.send_daily",
		"traquent.integrations.doctype.google_drive.google_drive.daily_backup",
	],
	"weekly_long": [
		"traquent.integrations.doctype.dropbox_settings.dropbox_settings.take_backups_weekly",
		"traquent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_weekly",
		"traquent.desk.form.document_follow.send_weekly_updates",
		"traquent.utils.change_log.check_for_update",
		"traquent.social.doctype.energy_point_log.energy_point_log.send_weekly_summary",
		"traquent.integrations.doctype.google_drive.google_drive.weekly_backup",
		"traquent.desk.doctype.changelog_feed.changelog_feed.fetch_changelog_feed",
	],
	"monthly": [
		"traquent.email.doctype.auto_email_report.auto_email_report.send_monthly",
		"traquent.social.doctype.energy_point_log.energy_point_log.send_monthly_summary",
	],
	"monthly_long": [
		"traquent.integrations.doctype.s3_backup_settings.s3_backup_settings.take_backups_monthly"
	],
}

sounds = [
	{"name": "email", "src": "/assets/traquent/sounds/email.mp3", "volume": 0.1},
	{"name": "submit", "src": "/assets/traquent/sounds/submit.mp3", "volume": 0.1},
	{"name": "cancel", "src": "/assets/traquent/sounds/cancel.mp3", "volume": 0.1},
	{"name": "delete", "src": "/assets/traquent/sounds/delete.mp3", "volume": 0.05},
	{"name": "click", "src": "/assets/traquent/sounds/click.mp3", "volume": 0.05},
	{"name": "error", "src": "/assets/traquent/sounds/error.mp3", "volume": 0.1},
	{"name": "alert", "src": "/assets/traquent/sounds/alert.mp3", "volume": 0.2},
	# {"name": "chime", "src": "/assets/traquent/sounds/chime.mp3"},
]

setup_wizard_exception = [
	"traquent.desk.page.setup_wizard.setup_wizard.email_setup_wizard_exception",
	"traquent.desk.page.setup_wizard.setup_wizard.log_setup_wizard_exception",
]

before_migrate = ["traquent.core.doctype.patch_log.patch_log.before_migrate"]
after_migrate = ["traquent.website.doctype.website_theme.website_theme.after_migrate"]

otp_methods = ["OTP App", "Email", "SMS"]

user_data_fields = [
	{"doctype": "Access Log", "strict": True},
	{"doctype": "Activity Log", "strict": True},
	{"doctype": "Comment", "strict": True},
	{
		"doctype": "Contact",
		"filter_by": "email_id",
		"redact_fields": ["first_name", "last_name", "phone", "mobile_no"],
		"rename": True,
	},
	{"doctype": "Contact Email", "filter_by": "email_id"},
	{
		"doctype": "Address",
		"filter_by": "email_id",
		"redact_fields": [
			"address_title",
			"address_line1",
			"address_line2",
			"city",
			"county",
			"state",
			"pincode",
			"phone",
			"fax",
		],
	},
	{
		"doctype": "Communication",
		"filter_by": "sender",
		"redact_fields": ["sender_full_name", "phone_no", "content"],
	},
	{"doctype": "Communication", "filter_by": "recipients"},
	{"doctype": "Email Group Member", "filter_by": "email"},
	{"doctype": "Email Unsubscribe", "filter_by": "email", "partial": True},
	{"doctype": "Email Queue", "filter_by": "sender"},
	{"doctype": "Email Queue Recipient", "filter_by": "recipient"},
	{
		"doctype": "File",
		"filter_by": "attached_to_name",
		"redact_fields": ["file_name", "file_url"],
	},
	{
		"doctype": "User",
		"filter_by": "name",
		"redact_fields": [
			"email",
			"username",
			"first_name",
			"middle_name",
			"last_name",
			"full_name",
			"birth_date",
			"user_image",
			"phone",
			"mobile_no",
			"location",
			"banner_image",
			"interest",
			"bio",
			"email_signature",
		],
	},
	{"doctype": "Version", "strict": True},
]

global_search_doctypes = {
	"Default": [
		{"doctype": "Contact"},
		{"doctype": "Address"},
		{"doctype": "ToDo"},
		{"doctype": "Note"},
		{"doctype": "Event"},
		{"doctype": "Blog Post"},
		{"doctype": "Dashboard"},
		{"doctype": "Country"},
		{"doctype": "Currency"},
		{"doctype": "Newsletter"},
		{"doctype": "Letter Head"},
		{"doctype": "Workflow"},
		{"doctype": "Web Page"},
		{"doctype": "Web Form"},
	]
}

override_whitelisted_methods = {
	# Legacy File APIs
	"traquent.utils.file_manager.download_file": "download_file",
	"traquent.core.doctype.file.file.download_file": "download_file",
	"traquent.core.doctype.file.file.unzip_file": "traquent.core.api.file.unzip_file",
	"traquent.core.doctype.file.file.get_attached_images": "traquent.core.api.file.get_attached_images",
	"traquent.core.doctype.file.file.get_files_in_folder": "traquent.core.api.file.get_files_in_folder",
	"traquent.core.doctype.file.file.get_files_by_search_text": "traquent.core.api.file.get_files_by_search_text",
	"traquent.core.doctype.file.file.get_max_file_size": "traquent.core.api.file.get_max_file_size",
	"traquent.core.doctype.file.file.create_new_folder": "traquent.core.api.file.create_new_folder",
	"traquent.core.doctype.file.file.move_file": "traquent.core.api.file.move_file",
	"traquent.core.doctype.file.file.zip_files": "traquent.core.api.file.zip_files",
	# Legacy (& Consistency) OAuth2 APIs
	"traquent.www.login.login_via_google": "traquent.integrations.oauth2_logins.login_via_google",
	"traquent.www.login.login_via_github": "traquent.integrations.oauth2_logins.login_via_github",
	"traquent.www.login.login_via_facebook": "traquent.integrations.oauth2_logins.login_via_facebook",
	"traquent.www.login.login_via_traquent": "traquent.integrations.oauth2_logins.login_via_traquent",
	"traquent.www.login.login_via_office365": "traquent.integrations.oauth2_logins.login_via_office365",
	"traquent.www.login.login_via_salesforce": "traquent.integrations.oauth2_logins.login_via_salesforce",
	"traquent.www.login.login_via_fairlogin": "traquent.integrations.oauth2_logins.login_via_fairlogin",
}

ignore_links_on_delete = [
	"Communication",
	"ToDo",
	"DocShare",
	"Email Unsubscribe",
	"Activity Log",
	"File",
	"Version",
	"Document Follow",
	"Comment",
	"View Log",
	"Tag Link",
	"Notification Log",
	"Email Queue",
	"Document Share Key",
	"Integration Request",
	"Unhandled Email",
	"Webhook Request Log",
	"Workspace",
	"Route History",
	"Access Log",
	"Permission Log",
]

# Request Hooks
before_request = [
	"traquent.recorder.record",
	"traquent.monitor.start",
	"traquent.rate_limiter.apply",
]

after_request = [
	"traquent.monitor.stop",
]

# Background Job Hooks
before_job = [
	"traquent.recorder.record",
	"traquent.monitor.start",
]

if os.getenv("traquent_SENTRY_DSN") and (
	os.getenv("ENABLE_SENTRY_DB_MONITORING") or os.getenv("SENTRY_TRACING_SAMPLE_RATE")
):
	before_request.append("traquent.utils.sentry.set_sentry_context")
	before_job.append("traquent.utils.sentry.set_sentry_context")

after_job = [
	"traquent.recorder.dump",
	"traquent.monitor.stop",
	"traquent.utils.file_lock.release_document_locks",
	"traquent.utils.background_jobs.flush_telemetry",
]

extend_bootinfo = [
	"traquent.utils.telemetry.add_bootinfo",
	"traquent.core.doctype.user_permission.user_permission.send_user_permissions",
]

get_changelog_feed = "traquent.desk.doctype.changelog_feed.changelog_feed.get_feed"

export_python_type_annotations = True

standard_navbar_items = [
	{
		"item_label": "User Settings",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.route_to_user()",
		"is_standard": 1,
	},
	{
		"item_label": "Workspace Settings",
		"item_type": "Action",
		"action": "traquent.quick_edit('Workspace Settings')",
		"is_standard": 1,
	},
	{
		"item_label": "Session Defaults",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.setup_session_defaults()",
		"is_standard": 1,
	},
	{
		"item_label": "Reload",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.clear_cache()",
		"is_standard": 1,
	},
	{
		"item_label": "View Website",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.view_website()",
		"is_standard": 1,
	},
	{
		"item_label": "Apps",
		"item_type": "Route",
		"route": "/apps",
		"is_standard": 1,
	},
	{
		"item_label": "Toggle Full Width",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.toggle_full_width()",
		"is_standard": 1,
	},
	{
		"item_label": "Toggle Theme",
		"item_type": "Action",
		"action": "new traquent.ui.ThemeSwitcher().show()",
		"is_standard": 1,
	},
	{
		"item_type": "Separator",
		"is_standard": 1,
		"item_label": "",
	},
	{
		"item_label": "Log out",
		"item_type": "Action",
		"action": "traquent.app.logout()",
		"is_standard": 1,
	},
]

standard_help_items = [
	{
		"item_label": "About",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.show_about()",
		"is_standard": 1,
	},
	{
		"item_label": "Keyboard Shortcuts",
		"item_type": "Action",
		"action": "traquent.ui.toolbar.show_shortcuts(event)",
		"is_standard": 1,
	},
	{
		"item_label": "System Health",
		"item_type": "Route",
		"route": "/app/system-health-report",
		"is_standard": 1,
	},
	{
		"item_label": "traquent Support",
		"item_type": "Route",
		"route": "https://traquent.io/support",
		"is_standard": 1,
	},
]

# log doctype cleanups to automatically add in log settings
default_log_clearing_doctypes = {
	"Error Log": 14,
	"Email Queue": 30,
	"Scheduled Job Log": 7,
	"Submission Queue": 7,
	"Prepared Report": 14,
	"Webhook Request Log": 30,
	"Unhandled Email": 30,
	"Reminder": 30,
	"Integration Request": 90,
	"Activity Log": 90,
	"Route History": 90,
}

# These keys will not be erased when doing traquent.clear_cache()
persistent_cache_keys = [
	"changelog-*",  # version update notifications
	"insert_queue_for_*",  # Deferred Insert
	"recorder-*",  # Recorder
	"global_search_queue",
]
