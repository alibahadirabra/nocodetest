// Copyright (c) 2020, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Console Log", {
	refresh: function (frm) {
		frm.add_custom_button(__("Re-Run in Console"), () => {
			window.localStorage.setItem("system_console_code", frm.doc.script);
			window.localStorage.setItem("system_console_type", frm.doc.type);
			traquent.set_route("Form", "System Console");
		});
	},
});
