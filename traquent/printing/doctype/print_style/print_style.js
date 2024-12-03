// Copyright (c) 2017, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Print Style", {
	refresh: function (frm) {
		frm.add_custom_button(__("Print Settings"), () => {
			traquent.set_route("Form", "Print Settings");
		});
	},
});
