// Copyright (c) 2019, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Google Settings", {
	refresh: function (frm) {
		frm.dashboard.set_headline(
			__("For more information, {0}.", [
				`<a href='https://traquent.com/docs/user/manual/en/traquent_integration/google_settings'>${__(
					"Click here"
				)}</a>`,
			])
		);
	},
});
