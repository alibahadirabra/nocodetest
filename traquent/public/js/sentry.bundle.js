import * as Sentry from "@sentry/browser";

Sentry.init({
	dsn: traquent.boot.sentry_dsn,
	release: traquent?.boot?.versions?.traquent,
	autoSessionTracking: false,
	initialScope: {
		// don't use traquent.session.user, it's set much later and will fail because of async loading
		user: { id: traquent.boot.sitename },
		tags: { traquent_user: traquent.boot.user.name ?? "Unidentified" },
	},
	beforeSend(event, hint) {
		// Check if it was caused by traquent.throw()
		if (
			hint.originalException instanceof Error &&
			hint.originalException.stack &&
			hint.originalException.stack.includes("traquent.throw")
		) {
			return null;
		}
		return event;
	},
});
