traquent.pages["backups"].on_page_load = function (wrapper) {
	var page = traquent.ui.make_app_page({
		parent: wrapper,
		title: __("Download Backups"),
		single_column: true,
	});

	page.add_inner_button(__("Set Number of Backups"), function () {
		traquent.set_route("Form", "System Settings");
	});

	page.add_inner_button(__("Download Files Backup"), function () {
		traquent.call({
			method: "traquent.desk.page.backups.backups.schedule_files_backup",
			args: { user_email: traquent.session.user_email },
		});
	});

	page.add_inner_button(__("Get Backup Encryption Key"), function () {
		if (traquent.user.has_role("System Manager")) {
			traquent.verify_password(function () {
				traquent.call({
					method: "traquent.utils.backups.get_backup_encryption_key",
					callback: function (r) {
						traquent.msgprint({
							title: __("Backup Encryption Key"),
							message: __(r.message),
							indicator: "blue",
						});
					},
				});
			});
		} else {
			traquent.msgprint({
				title: __("Error"),
				message: __("System Manager privileges required."),
				indicator: "red",
			});
		}
	});

	traquent.breadcrumbs.add("Setup");

	$(traquent.render_template("backups")).appendTo(page.body.addClass("no-border"));
};
