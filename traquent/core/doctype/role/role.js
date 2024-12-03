// Copyright (c) 2022, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See LICENSE

traquent.ui.form.on("Role", {
	refresh: function (frm) {
		if (frm.doc.name === "All") {
			frm.dashboard.add_comment(
				__("Role 'All' will be given to all system + website users."),
				"yellow"
			);
		} else if (frm.doc.name === "Desk User") {
			frm.dashboard.add_comment(
				__("Role 'Desk User' will be given to all system users."),
				"yellow"
			);
		}

		frm.set_df_property("is_custom", "read_only", traquent.session.user !== "Administrator");

		frm.add_custom_button("Role Permissions Manager", function () {
			traquent.route_options = { role: frm.doc.name };
			traquent.set_route("permission-manager");
		});
		frm.add_custom_button("Show Users", function () {
			traquent.route_options = { role: frm.doc.name };
			traquent.set_route("List", "User", "Report");
		});
	},
});
