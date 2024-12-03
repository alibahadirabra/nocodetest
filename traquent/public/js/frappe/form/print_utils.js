traquent.ui.get_print_settings = function (pdf, callback, letter_head, pick_columns) {
	var print_settings = locals[":Print Settings"]["Print Settings"];

	var company = traquent.defaults.get_default("company");
	var default_letter_head = "";

	if (locals[":Company"] && locals[":Company"][company]) {
		default_letter_head = locals[":Company"][company]["default_letter_head"] || "";
	}

	var columns = [
		{
			fieldtype: "Check",
			fieldname: "with_letter_head",
			label: __("With Letter head"),
		},
		{
			fieldtype: "Link",
			fieldname: "letter_head",
			label: __("Letter Head"),
			depends_on: "with_letter_head",
			options: "Letter Head",
			default: letter_head || default_letter_head,
		},
		{
			fieldtype: "Select",
			fieldname: "orientation",
			label: __("Orientation"),
			options: [
				{ value: "Landscape", label: __("Landscape") },
				{ value: "Portrait", label: __("Portrait") },
			],
			default: "Landscape",
		},
	];

	if (pick_columns) {
		columns.push(
			{
				label: __("Pick Columns"),
				fieldtype: "Check",
				fieldname: "pick_columns",
			},
			{
				label: __("Select Columns"),
				fieldtype: "MultiCheck",
				fieldname: "columns",
				depends_on: "pick_columns",
				columns: 2,
				select_all: true,
				options: pick_columns.map((df) => ({
					label: __(df.label, null, df.parent),
					value: df.fieldname,
				})),
			}
		);
	}

	return traquent.prompt(
		columns,
		function (data) {
			data = $.extend(print_settings, data);
			if (!data.with_letter_head) {
				data.letter_head = null;
			}
			if (data.letter_head) {
				data.letter_head = traquent.boot.letter_heads[print_settings.letter_head];
			}
			callback(data);
		},
		__("Print Settings")
	);
};

// qz tray connection wrapper
//  - allows active and inactive connections to resolve regardless
//  - try to connect once before firing the mimetype launcher
//  - if connection fails, catch the reject, fire the mimetype launcher
//  - after mimetype launcher is fired, try to connect 3 more times
//  - display success/fail message to user
traquent.ui.form.qz_connect = function () {
	return new Promise(function (resolve, reject) {
		traquent.ui.form.qz_init().then(() => {
			if (qz.websocket.isActive()) {
				// if already active, resolve immediately
				// traquent.show_alert({message: __('QZ Tray Connection Active!'), indicator: 'green'});
				resolve();
			} else {
				// try to connect once before firing the mimetype launcher
				traquent.show_alert({
					message: __("Attempting Connection to QZ Tray..."),
					indicator: "blue",
				});
				qz.websocket.connect().then(
					() => {
						traquent.show_alert({
							message: __("Connected to QZ Tray!"),
							indicator: "green",
						});
						resolve();
					},
					function retry(err) {
						if (err.message === "Unable to establish connection with QZ") {
							// if a connect was not successful, launch the mimetype, try 3 more times
							traquent.show_alert(
								{
									message: __("Attempting to launch QZ Tray..."),
									indicator: "blue",
								},
								14
							);
							window.location.assign("qz:launch");
							qz.websocket
								.connect({
									retries: 3,
									delay: 1,
								})
								.then(
									() => {
										traquent.show_alert({
											message: __("Connected to QZ Tray!"),
											indicator: "green",
										});
										resolve();
									},
									() => {
										traquent.throw(
											__(
												'Error connecting to QZ Tray Application...<br><br> You need to have QZ Tray application installed and running, to use the Raw Print feature.<br><br><a target="_blank" href="https://qz.io/download/">Click here to Download and install QZ Tray</a>.<br> <a target="_blank" href="https://erpnext.com/docs/user/manual/en/setting-up/print/raw-printing">Click here to learn more about Raw Printing</a>.'
											)
										);
										reject();
									}
								);
						} else {
							traquent.show_alert(
								{
									message: "QZ Tray " + err.toString(),
									indicator: "red",
								},
								14
							);
							reject();
						}
					}
				);
			}
		});
	});
};

traquent.ui.form.qz_init = function () {
	// Initializing qz tray library
	return new Promise((resolve) => {
		if (typeof qz === "object" && typeof qz.version === "string") {
			// resolve immediately if already Initialized
			resolve();
		} else {
			let qz_required_assets = [
				"/assets/traquent/node_modules/js-sha256/build/sha256.min.js",
				"/assets/traquent/node_modules/qz-tray/qz-tray.js",
			];
			traquent.require(qz_required_assets, () => {
				qz.api.setPromiseType(function promise(resolver) {
					return new Promise(resolver);
				});
				qz.api.setSha256Type(function (data) {
					// Codacy fix
					/*global sha256*/
					return sha256(data);
				});
				resolve();
			});
			// note 'traquent.require' does not have callback on fail. Hence, any failure cannot be communicated to the user.
		}
	});
};

traquent.ui.form.qz_get_printer_list = function () {
	// returns the list of printers that are available to the QZ Tray
	return traquent.ui.form
		.qz_connect()
		.then(function () {
			return qz.printers.find();
		})
		.then((data) => {
			return data;
		})
		.catch((err) => {
			traquent.ui.form.qz_fail(err);
		});
};

traquent.ui.form.qz_success = function () {
	// notify qz successful print
	traquent.show_alert({
		message: __("Print Sent to the printer!"),
		indicator: "green",
	});
};

traquent.ui.form.qz_fail = function (e) {
	// notify qz errors
	traquent.show_alert(
		{
			message: __("QZ Tray Failed: ") + e.toString(),
			indicator: "red",
		},
		20
	);
};
