// Copyright (c) 2020, traquent Technologies and contributors
// For license information, please see license.txt

traquent.ui.form.on("Navbar Settings", {
	after_save: function (frm) {
		traquent.ui.toolbar.clear_cache();
	},
});
