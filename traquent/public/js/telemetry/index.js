import "../lib/posthog.js";

class TelemetryManager {
	constructor() {
		this.enabled = false;

		this.project_id = traquent.boot.posthog_project_id;
		this.telemetry_host = traquent.boot.posthog_host;
		this.site_age = traquent.boot.telemetry_site_age;
		if (cint(traquent.boot.enable_telemetry) && this.project_id && this.telemetry_host) {
			this.enabled = true;
		}
	}

	initialize() {
		if (!this.enabled) return;
		let disable_decide = !this.should_record_session();
		try {
			posthog.init(this.project_id, {
				api_host: this.telemetry_host,
				autocapture: false,
				capture_pageview: false,
				capture_pageleave: false,
				advanced_disable_decide: disable_decide,
			});
			posthog.identify(traquent.boot.sitename);
			this.send_heartbeat();
			this.register_pageview_handler();
		} catch (e) {
			console.trace("Failed to initialize telemetry", e);
			this.enabled = false;
		}
	}

	capture(event, app, props) {
		if (!this.enabled) return;
		posthog.capture(`${app}_${event}`, props);
	}

	disable() {
		this.enabled = false;
	}

	can_enable() {
		if (cint(navigator.doNotTrack)) {
			return false;
		}
		let posthog_available = Boolean(this.telemetry_host && this.project_id);
		let sentry_available = Boolean(traquent.boot.sentry_dsn);
		return posthog_available || sentry_available;
	}

	send_heartbeat() {
		const KEY = "ph_last_heartbeat";
		const now = traquent.datetime.system_datetime(true);
		const last = localStorage.getItem(KEY);

		if (!last || moment(now).diff(moment(last), "hours") > 12) {
			localStorage.setItem(KEY, now.toISOString());
			this.capture("heartbeat", "traquent", { traquent_version: traquent.boot?.versions?.traquent });
		}
	}

	register_pageview_handler() {
		if (this.site_age && this.site_age > 6) {
			return;
		}

		traquent.router.on("change", () => {
			posthog.capture("$pageview");
		});
	}

	should_record_session() {
		let start = traquent.boot.sysdefaults.session_recording_start;
		if (!start) return;

		let start_datetime = traquent.datetime.str_to_obj(start);
		let now = traquent.datetime.now_datetime();
		// if user allowed recording only record for first 2 hours, never again.
		return traquent.datetime.get_minute_diff(now, start_datetime) < 120;
	}
}

traquent.telemetry = new TelemetryManager();
traquent.telemetry.initialize();
