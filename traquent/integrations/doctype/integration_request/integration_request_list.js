traquent.listview_settings["Integration Request"] = {
	onload: function (list_view) {
		traquent.require("logtypes.bundle.js", () => {
			traquent.utils.logtypes.show_log_retention_message(list_view.doctype);
		});
	},
};