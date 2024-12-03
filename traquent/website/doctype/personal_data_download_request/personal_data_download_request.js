// Copyright (c) 2019, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Personal Data Download Request", {
	onload: function (frm) {
		if (frm.is_new()) {
			frm.doc.user = traquent.session.user;
		}
	},
});
