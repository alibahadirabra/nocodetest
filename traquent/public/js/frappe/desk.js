// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt
/* eslint-disable no-console */

// __('Modules') __('Domains') __('Places') __('Administration') # for translation, don't remove

traquent.start_app = function () {
	if (!traquent.Application) return;
	traquent.assets.check();
	traquent.provide("traquent.app");
	traquent.provide("traquent.desk");
	traquent.app = new traquent.Application();
};

$(document).ready(function () {
	if (!traquent.utils.supportsES6) {
		traquent.msgprint({
			indicator: "red",
			title: __("Browser not supported"),
			message: __(
				"Some of the features might not work in your browser. Please update your browser to the latest version."
			),
		});
	}
	traquent.start_app();
});

traquent.Application = class Application {
	constructor() {
		this.startup();
	}

	startup() {
		traquent.realtime.init();
		traquent.model.init();

		this.load_bootinfo();
		this.load_user_permissions();
		this.make_nav_bar();
		this.make_sidebar();
		this.set_favicon();
		this.set_fullwidth_if_enabled();
		this.add_browser_class();
		this.setup_energy_point_listeners();
		this.setup_copy_doc_listener();
		this.setup_broadcast_listeners();

		traquent.ui.keys.setup();

		this.setup_theme();

		// page container
		this.make_page_container();
		this.setup_tours();
		this.set_route();

		// trigger app startup
		$(document).trigger("startup");
		$(document).trigger("app_ready");

		this.show_notices();
		this.show_notes();

		if (traquent.ui.startup_setup_dialog && !traquent.boot.setup_complete) {
			traquent.ui.startup_setup_dialog.pre_show();
			traquent.ui.startup_setup_dialog.show();
		}

		// listen to build errors
		this.setup_build_events();

		if (traquent.sys_defaults.email_user_password) {
			var email_list = traquent.sys_defaults.email_user_password.split(",");
			for (var u in email_list) {
				if (email_list[u] === traquent.user.name) {
					this.set_password(email_list[u]);
				}
			}
		}

		// REDESIGN-TODO: Fix preview popovers
		this.link_preview = new traquent.ui.LinkPreview();

		traquent.broadcast.emit("boot", {
			csrf_token: traquent.csrf_token,
			user: traquent.session.user,
		});
	}

	make_sidebar() {
		this.sidebar = new traquent.ui.Sidebar({});
	}

	setup_theme() {
		traquent.ui.keys.add_shortcut({
			shortcut: "shift+ctrl+g",
			description: __("Switch Theme"),
			action: () => {
				if (traquent.theme_switcher && traquent.theme_switcher.dialog.is_visible) {
					traquent.theme_switcher.hide();
				} else {
					traquent.theme_switcher = new traquent.ui.ThemeSwitcher();
					traquent.theme_switcher.show();
				}
			},
		});

		traquent.ui.add_system_theme_switch_listener();
		const root = document.documentElement;

		const observer = new MutationObserver(() => {
			traquent.ui.set_theme();
		});
		observer.observe(root, {
			attributes: true,
			attributeFilter: ["data-theme-mode"],
		});

		traquent.ui.set_theme();
	}

	setup_tours() {
		if (
			!window.Cypress &&
			traquent.boot.onboarding_tours &&
			traquent.boot.user.onboarding_status != null
		) {
			let pending_tours = !traquent.boot.onboarding_tours.every(
				(tour) => traquent.boot.user.onboarding_status[tour[0]]?.is_complete
			);
			if (pending_tours && traquent.boot.onboarding_tours.length > 0) {
				traquent.require("onboarding_tours.bundle.js", () => {
					traquent.utils.sleep(1000).then(() => {
						traquent.ui.init_onboarding_tour();
					});
				});
			}
		}
	}

	show_notices() {
		if (traquent.boot.messages) {
			traquent.msgprint(traquent.boot.messages);
		}

		if (traquent.user_roles.includes("System Manager")) {
			// delayed following requests to make boot faster
			setTimeout(() => {
				this.show_change_log();
				this.show_update_available();
			}, 1000);
		}

		if (!traquent.boot.developer_mode) {
			let console_security_message = __(
				"Using this console may allow attackers to impersonate you and steal your information. Do not enter or paste code that you do not understand."
			);
			console.log(`%c${console_security_message}`, "font-size: large");
		}

		traquent.realtime.on("version-update", function () {
			var dialog = traquent.msgprint({
				message: __(
					"The application has been updated to a new version, please refresh this page"
				),
				indicator: "green",
				title: __("Version Updated"),
			});
			dialog.set_primary_action(__("Refresh"), function () {
				location.reload(true);
			});
			dialog.get_close_btn().toggle(false);
		});
	}

	set_route() {
		if (traquent.boot && localStorage.getItem("session_last_route")) {
			traquent.set_route(localStorage.getItem("session_last_route"));
			localStorage.removeItem("session_last_route");
		} else {
			// route to home page
			traquent.router.route();
		}
		traquent.router.on("change", () => {
			$(".tooltip").hide();
		});
	}

	set_password(user) {
		var me = this;
		traquent.call({
			method: "traquent.core.doctype.user.user.get_email_awaiting",
			args: {
				user: user,
			},
			callback: function (email_account) {
				email_account = email_account["message"];
				if (email_account) {
					var i = 0;
					if (i < email_account.length) {
						me.email_password_prompt(email_account, user, i);
					}
				}
			},
		});
	}

	email_password_prompt(email_account, user, i) {
		var me = this;
		const email_id = email_account[i]["email_id"];
		let d = new traquent.ui.Dialog({
			title: __("Password missing in Email Account"),
			fields: [
				{
					fieldname: "password",
					fieldtype: "Password",
					label: __(
						"Please enter the password for: <b>{0}</b>",
						[email_id],
						"Email Account"
					),
					reqd: 1,
				},
				{
					fieldname: "submit",
					fieldtype: "Button",
					label: __("Submit", null, "Submit password for Email Account"),
				},
			],
		});
		d.get_input("submit").on("click", function () {
			//setup spinner
			d.hide();
			var s = new traquent.ui.Dialog({
				title: __("Checking one moment"),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "checking",
					},
				],
			});
			s.fields_dict.checking.$wrapper.html('<i class="fa fa-spinner fa-spin fa-4x"></i>');
			s.show();
			traquent.call({
				method: "traquent.email.doctype.email_account.email_account.set_email_password",
				args: {
					email_account: email_account[i]["email_account"],
					password: d.get_value("password"),
				},
				callback: function (passed) {
					s.hide();
					d.hide(); //hide waiting indication
					if (!passed["message"]) {
						traquent.show_alert(
							{ message: __("Login Failed please try again"), indicator: "error" },
							5
						);
						me.email_password_prompt(email_account, user, i);
					} else {
						if (i + 1 < email_account.length) {
							i = i + 1;
							me.email_password_prompt(email_account, user, i);
						}
					}
				},
			});
		});
		d.show();
	}
	load_bootinfo() {
		if (traquent.boot) {
			this.setup_workspaces();
			traquent.model.sync(traquent.boot.docs);
			this.check_metadata_cache_status();
			this.set_globals();
			this.sync_pages();
			traquent.router.setup();
			this.setup_moment();
			if (traquent.boot.print_css) {
				traquent.dom.set_style(traquent.boot.print_css, "print-style");
			}
			traquent.user.name = traquent.boot.user.name;
			traquent.router.setup();
		} else {
			this.set_as_guest();
		}
	}

	setup_workspaces() {
		traquent.modules = {};
		traquent.workspaces = {};
		traquent.boot.allowed_workspaces = traquent.boot.sidebar_pages.pages;

		for (let page of traquent.boot.allowed_workspaces || []) {
			traquent.modules[page.module] = page;
			traquent.workspaces[traquent.router.slug(page.name)] = page;
		}
	}

	load_user_permissions() {
		traquent.defaults.load_user_permission_from_boot();

		traquent.realtime.on(
			"update_user_permissions",
			traquent.utils.debounce(() => {
				traquent.defaults.update_user_permissions();
			}, 500)
		);
	}

	check_metadata_cache_status() {
		if (traquent.boot.metadata_version != localStorage.metadata_version) {
			traquent.assets.clear_local_storage();
			traquent.assets.init_local_storage();
		}
	}

	set_globals() {
		traquent.session.user = traquent.boot.user.name;
		traquent.session.logged_in_user = traquent.boot.user.name;
		traquent.session.user_email = traquent.boot.user.email;
		traquent.session.user_fullname = traquent.user_info().fullname;

		traquent.user_defaults = traquent.boot.user.defaults;
		traquent.user_roles = traquent.boot.user.roles;
		traquent.sys_defaults = traquent.boot.sysdefaults;

		traquent.ui.py_date_format = traquent.boot.sysdefaults.date_format
			.replace("dd", "%d")
			.replace("mm", "%m")
			.replace("yyyy", "%Y");
		traquent.boot.user.last_selected_values = {};
	}
	sync_pages() {
		// clear cached pages if timestamp is not found
		if (localStorage["page_info"]) {
			traquent.boot.allowed_pages = [];
			var page_info = JSON.parse(localStorage["page_info"]);
			$.each(traquent.boot.page_info, function (name, p) {
				if (!page_info[name] || page_info[name].modified != p.modified) {
					delete localStorage["_page:" + name];
				}
				traquent.boot.allowed_pages.push(name);
			});
		} else {
			traquent.boot.allowed_pages = Object.keys(traquent.boot.page_info);
		}
		localStorage["page_info"] = JSON.stringify(traquent.boot.page_info);
	}
	set_as_guest() {
		traquent.session.user = "Guest";
		traquent.session.user_email = "";
		traquent.session.user_fullname = "Guest";

		traquent.user_defaults = {};
		traquent.user_roles = ["Guest"];
		traquent.sys_defaults = {};
	}
	make_page_container() {
		if ($("#body").length) {
			$(".splash").remove();
			traquent.temp_container = $("<div id='temp-container' style='display: none;'>").appendTo(
				"body"
			);
			traquent.container = new traquent.views.Container();
		}
	}
	make_nav_bar() {
		// toolbar
		if (traquent.boot && traquent.boot.home_page !== "setup-wizard") {
			traquent.traquent_toolbar = new traquent.ui.toolbar.Toolbar();
		}
	}
	logout() {
		var me = this;
		me.logged_out = true;
		return traquent.call({
			method: "logout",
			callback: function (r) {
				if (r.exc) {
					return;
				}
				me.redirect_to_login();
			},
		});
	}
	handle_session_expired() {
		traquent.app.redirect_to_login();
	}
	redirect_to_login() {
		window.location.href = `/login?redirect-to=${encodeURIComponent(
			window.location.pathname + window.location.search
		)}`;
	}
	set_favicon() {
		var link = $('link[type="image/x-icon"]').remove().attr("href");
		$('<link rel="shortcut icon" href="' + link + '" type="image/x-icon">').appendTo("head");
		$('<link rel="icon" href="' + link + '" type="image/x-icon">').appendTo("head");
	}
	trigger_primary_action() {
		// to trigger change event on active input before triggering primary action
		$(document.activeElement).blur();
		// wait for possible JS validations triggered after blur (it might change primary button)
		setTimeout(() => {
			if (window.cur_dialog && cur_dialog.display && !cur_dialog.is_minimized) {
				// trigger primary
				cur_dialog.get_primary_btn().trigger("click");
			} else if (cur_frm && cur_frm.page.btn_primary.is(":visible")) {
				cur_frm.page.btn_primary.trigger("click");
			} else if (traquent.container.page.save_action) {
				traquent.container.page.save_action();
			}
		}, 100);
	}

	show_change_log() {
		var me = this;
		let change_log = traquent.boot.change_log;

		// traquent.boot.change_log = [{
		// 	"change_log": [
		// 		[<version>, <change_log in markdown>],
		// 		[<version>, <change_log in markdown>],
		// 	],
		// 	"description": "ERP made simple",
		// 	"title": "traquent",
		// 	"version": "12.2.0"
		// }];

		if (
			!Array.isArray(change_log) ||
			!change_log.length ||
			window.Cypress ||
			cint(traquent.boot.sysdefaults.disable_change_log_notification)
		) {
			return;
		}

		// Iterate over changelog
		var change_log_dialog = traquent.msgprint({
			message: traquent.render_template("change_log", { change_log: change_log }),
			title: __("Updated To A New Version 🎉"),
			wide: true,
		});
		change_log_dialog.keep_open = true;
		change_log_dialog.custom_onhide = function () {
			traquent.call({
				method: "traquent.utils.change_log.update_last_known_versions",
			});
			me.show_notes();
		};
	}

	show_update_available() {
		if (!traquent.boot.has_app_updates) return;
		traquent.xcall("traquent.utils.change_log.show_update_popup");
	}

	add_browser_class() {
		$("html").addClass(traquent.utils.get_browser().name.toLowerCase());
	}

	set_fullwidth_if_enabled() {
		traquent.ui.toolbar.set_fullwidth_if_enabled();
	}

	show_notes() {
		var me = this;
		if (traquent.boot.notes.length) {
			traquent.boot.notes.forEach(function (note) {
				if (!note.seen || note.notify_on_every_login) {
					var d = traquent.msgprint({ message: note.content, title: note.title });
					d.keep_open = true;
					d.custom_onhide = function () {
						note.seen = true;

						// Mark note as read if the Notify On Every Login flag is not set
						if (!note.notify_on_every_login) {
							traquent.call({
								method: "traquent.desk.doctype.note.note.mark_as_seen",
								args: {
									note: note.name,
								},
							});
						}

						// next note
						me.show_notes();
					};
				}
			});
		}
	}

	setup_build_events() {
		if (traquent.boot.developer_mode) {
			traquent.require("build_events.bundle.js");
		}
	}

	setup_energy_point_listeners() {
		traquent.realtime.on("energy_point_alert", (message) => {
			traquent.show_alert(message);
		});
	}

	setup_copy_doc_listener() {
		$("body").on("paste", (e) => {
			try {
				let pasted_data = traquent.utils.get_clipboard_data(e);
				let doc = JSON.parse(pasted_data);
				if (doc.doctype) {
					e.preventDefault();
					const sleep = traquent.utils.sleep;

					traquent.dom.freeze(__("Creating {0}", [doc.doctype]) + "...");
					// to avoid abrupt UX
					// wait for activity feedback
					sleep(500).then(() => {
						let res = traquent.model.with_doctype(doc.doctype, () => {
							let newdoc = traquent.model.copy_doc(doc);
							newdoc.__newname = doc.name;
							delete doc.name;
							newdoc.idx = null;
							newdoc.__run_link_triggers = false;
							traquent.set_route("Form", newdoc.doctype, newdoc.name);
							traquent.dom.unfreeze();
						});
						res && res.fail?.(traquent.dom.unfreeze);
					});
				}
			} catch (e) {
				//
			}
		});
	}

	/// Setup event listeners for events across browser tabs / web workers.
	setup_broadcast_listeners() {
		// booted in another tab -> refresh csrf to avoid invalid requests.
		traquent.broadcast.on("boot", ({ csrf_token, user }) => {
			if (user && user != traquent.session.user) {
				traquent.msgprint({
					message: __(
						"You've logged in as another user from another tab. Refresh this page to continue using system."
					),
					title: __("User Changed"),
					primary_action: {
						label: __("Refresh"),
						action: () => {
							window.location.reload();
						},
					},
				});
				return;
			}

			if (csrf_token) {
				// If user re-logged in then their other tabs won't be usable without this update.
				traquent.csrf_token = csrf_token;
			}
		});
	}

	setup_moment() {
		moment.updateLocale("en", {
			week: {
				dow: traquent.datetime.get_first_day_of_the_week_index(),
			},
		});
		moment.locale("en");
		moment.user_utc_offset = moment().utcOffset();
		if (traquent.boot.timezone_info) {
			moment.tz.add(traquent.boot.timezone_info);
		}
	}
};

traquent.get_module = function (m, default_module) {
	var module = traquent.modules[m] || default_module;
	if (!module) {
		return;
	}

	if (module._setup) {
		return module;
	}

	if (!module.label) {
		module.label = m;
	}

	if (!module._label) {
		module._label = __(module.label);
	}

	module._setup = true;

	return module;
};
