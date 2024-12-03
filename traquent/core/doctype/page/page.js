// Copyright (c) 2016, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Page", {
	refresh: function (frm) {
		if (!traquent.boot.developer_mode && traquent.session.user != "Administrator") {
			// make the document read-only
			frm.set_read_only();
		}
		if (!frm.is_new() && !frm.doc.istable) {
			frm.add_custom_button(__("Go to {0} Page", [frm.doc.title || frm.doc.name]), () => {
				traquent.set_route(frm.doc.name);
			});
		}
	},
});
