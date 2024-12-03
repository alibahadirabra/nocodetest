// Copyright (c) 2019, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Access Log", {
	show_document: function (frm) {
		traquent.set_route("Form", frm.doc.export_from, frm.doc.reference_document);
	},

	show_report: function (frm) {
		if (frm.doc.report_name.includes("/")) {
			traquent.set_route(frm.doc.report_name);
		} else {
			let filters = frm.doc.filters ? JSON.parse(frm.doc.filters) : {};
			traquent.set_route("query-report", frm.doc.report_name, filters);
		}
	},
});
