traquent.listview_settings["Workflow"] = {
	add_fields: ["is_active"],
	get_indicator: function (doc) {
		if (doc.is_active) {
			return [__("Active"), "green", "is_active,=,Yes"];
		} else if (!doc.is_active) {
			return [__("Not active"), "gray", "is_active,=,No"];
		}
	},
	button: {
		show(doc) {
			return doc.name;
		},
		get_label() {
			return traquent.utils.icon("workflow", "sm");
		},
		get_description(doc) {
			return __("Build {0}", [`${doc.name}`]);
		},
		action(doc) {
			traquent.set_route("workflow-builder", doc.name);
		},
	},
};

traquent.help.youtube_id["Workflow"] = "yObJUg9FxFs";
