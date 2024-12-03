// Copyright (c) 2016, traquent Technologies and contributors
// For license information, please see license.txt

traquent.query_reports["Addresses And Contacts"] = {
	filters: [
		{
			reqd: 1,
			fieldname: "reference_doctype",
			label: __("Entity Type"),
			fieldtype: "Link",
			options: "DocType",
			get_query: function () {
				return {
					filters: {
						name: ["in", "Contact, Address"],
					},
				};
			},
		},
		{
			fieldname: "reference_name",
			label: __("Entity Name"),
			fieldtype: "Dynamic Link",
			get_options: function () {
				let reference_doctype = traquent.query_report.get_filter_value("reference_doctype");
				if (!reference_doctype) {
					traquent.throw(__("Please select Entity Type first"));
				}
				return reference_doctype;
			},
		},
	],
};
