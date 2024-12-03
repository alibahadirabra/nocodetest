// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// provide a namespace
if (!window.traquent) window.traquent = {};

traquent.provide = function (namespace) {
	// docs: create a namespace //
	var nsl = namespace.split(".");
	var parent = window;
	for (var i = 0; i < nsl.length; i++) {
		var n = nsl[i];
		if (!parent[n]) {
			parent[n] = {};
		}
		parent = parent[n];
	}
	return parent;
};

traquent.provide("locals");
traquent.provide("traquent.flags");
traquent.provide("traquent.settings");
traquent.provide("traquent.utils");
traquent.provide("traquent.ui.form");
traquent.provide("traquent.modules");
traquent.provide("traquent.templates");
traquent.provide("traquent.test_data");
traquent.provide("traquent.utils");
traquent.provide("traquent.model");
traquent.provide("traquent.user");
traquent.provide("traquent.session");
traquent.provide("traquent._messages");
traquent.provide("locals.DocType");

// for listviews
traquent.provide("traquent.listview_settings");
traquent.provide("traquent.tour");
traquent.provide("traquent.listview_parent_route");

// constants
window.NEWLINE = "\n";
window.TAB = 9;
window.UP_ARROW = 38;
window.DOWN_ARROW = 40;

// proxy for user globals defined in desk.js

// API globals
window.cur_frm = null;
