// Copyright (c) 2017, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Activity Log", {
	refresh: function (frm) {
		// Nothing in this form is supposed to be editable.
		frm.disable_form();
	},
});
