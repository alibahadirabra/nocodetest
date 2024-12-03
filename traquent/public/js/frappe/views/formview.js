// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

traquent.provide("traquent.views.formview");

traquent.views.FormFactory = class FormFactory extends traquent.views.Factory {
	make(route) {
		var doctype = route[1],
			doctype_layout = traquent.router.doctype_layout || doctype;

		if (!traquent.views.formview[doctype_layout]) {
			traquent.model.with_doctype(doctype, () => {
				this.page = traquent.container.add_page(doctype_layout);
				traquent.views.formview[doctype_layout] = this.page;
				this.make_and_show(doctype, route);
			});
		} else {
			this.show_doc(route);
		}

		this.setup_events();
	}

	make_and_show(doctype, route) {
		if (traquent.router.doctype_layout) {
			traquent.model.with_doc("DocType Layout", traquent.router.doctype_layout, () => {
				this.make_form(doctype);
				this.show_doc(route);
			});
		} else {
			this.make_form(doctype);
			this.show_doc(route);
		}
	}

	make_form(doctype) {
		this.page.frm = new traquent.ui.form.Form(
			doctype,
			this.page,
			true,
			traquent.router.doctype_layout
		);
	}

	setup_events() {
		if (!this.initialized) {
			$(document).on("page-change", function () {
				traquent.ui.form.close_grid_form();
			});
		}
		this.initialized = true;
	}

	show_doc(route) {
		var doctype = route[1],
			doctype_layout = traquent.router.doctype_layout || doctype,
			name = route.slice(2).join("/");

		if (traquent.model.new_names[name]) {
			// document has been renamed, reroute
			name = traquent.model.new_names[name];
			traquent.set_route("Form", doctype_layout, name);
			return;
		}

		const doc = traquent.get_doc(doctype, name);
		if (
			doc &&
			traquent.model.get_docinfo(doctype, name) &&
			(doc.__islocal || traquent.model.is_fresh(doc))
		) {
			// is document available and recent?
			this.render(doctype_layout, name);
		} else {
			this.fetch_and_render(doctype, name, doctype_layout);
		}
	}

	fetch_and_render(doctype, name, doctype_layout) {
		traquent.model.with_doc(doctype, name, (name, r) => {
			if (r && r["403"]) return; // not permitted

			if (!(locals[doctype] && locals[doctype][name])) {
				if (name && name.substr(0, 3) === "new") {
					this.render_new_doc(doctype, name, doctype_layout);
				} else {
					traquent.show_not_found();
				}
				return;
			}
			this.render(doctype_layout, name);
		});
	}

	render_new_doc(doctype, name, doctype_layout) {
		const new_name = traquent.model.make_new_doc_and_get_name(doctype, true);
		if (new_name === name) {
			this.render(doctype_layout, name);
		} else {
			traquent.route_flags.replace_route = true;
			traquent.set_route("Form", doctype_layout, new_name);
		}
	}

	render(doctype_layout, name) {
		traquent.container.change_to(doctype_layout);
		traquent.views.formview[doctype_layout].frm.refresh(name);
	}
};
