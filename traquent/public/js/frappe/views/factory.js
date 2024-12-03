// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

traquent.provide("traquent.pages");
traquent.provide("traquent.views");

traquent.views.Factory = class Factory {
	constructor(opts) {
		$.extend(this, opts);
	}

	show() {
		this.route = traquent.get_route();
		this.page_name = traquent.get_route_str();

		if (this.before_show && this.before_show() === false) return;

		if (traquent.pages[this.page_name]) {
			traquent.container.change_to(this.page_name);
			if (this.on_show) {
				this.on_show();
			}
		} else {
			if (this.route[1]) {
				this.make(this.route);
			} else {
				traquent.show_not_found(this.route);
			}
		}
	}

	make_page(double_column, page_name, sidebar_postition) {
		return traquent.make_page(double_column, page_name, sidebar_postition);
	}
};

traquent.make_page = function (double_column, page_name, sidebar_position) {
	if (!page_name) {
		page_name = traquent.get_route_str();
	}

	const page = traquent.container.add_page(page_name);

	traquent.ui.make_app_page({
		parent: page,
		single_column: !double_column,
		sidebar_position: sidebar_position,
	});

	traquent.container.change_to(page_name);
	return page;
};
