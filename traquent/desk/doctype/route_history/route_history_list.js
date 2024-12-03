traquent.listview_settings["Route History"] = {
	onload: function (listview) {
		traquent.require("logtypes.bundle.js", () => {
			traquent.utils.logtypes.show_log_retention_message(cur_list.doctype);
		});
	},
};
