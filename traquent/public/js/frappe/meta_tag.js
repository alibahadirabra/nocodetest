traquent.provide("traquent.model");
traquent.provide("traquent.utils");

/**
 * Opens the Website Meta Tag form if it exists for {route}
 * or creates a new doc and opens the form
 */
traquent.utils.set_meta_tag = function (route) {
	traquent.db.exists("Website Route Meta", route).then((exists) => {
		if (exists) {
			traquent.set_route("Form", "Website Route Meta", route);
		} else {
			// new doc
			const doc = traquent.model.get_new_doc("Website Route Meta");
			doc.__newname = route;
			traquent.set_route("Form", doc.doctype, doc.name);
		}
	});
};
