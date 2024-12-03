traquent.user_info = function (uid) {
	if (!uid) uid = traquent.session.user;

	let user_info;
	if (!(traquent.boot.user_info && traquent.boot.user_info[uid])) {
		user_info = { fullname: uid || "Unknown" };
	} else {
		user_info = traquent.boot.user_info[uid];
	}

	user_info.abbr = traquent.get_abbr(user_info.fullname);
	user_info.color = traquent.get_palette(user_info.fullname);

	return user_info;
};

traquent.update_user_info = function (user_info) {
	for (let user in user_info) {
		if (traquent.boot.user_info[user]) {
			Object.assign(traquent.boot.user_info[user], user_info[user]);
		} else {
			traquent.boot.user_info[user] = user_info[user];
		}
	}
};

traquent.provide("traquent.user");

$.extend(traquent.user, {
	name: "Guest",
	full_name: function (uid) {
		return uid === traquent.session.user
			? __(
					"You",
					null,
					"Name of the current user. For example: You edited this 5 hours ago."
			  )
			: traquent.user_info(uid).fullname;
	},
	image: function (uid) {
		return traquent.user_info(uid).image;
	},
	abbr: function (uid) {
		return traquent.user_info(uid).abbr;
	},
	has_role: function (rl) {
		if (typeof rl == "string") rl = [rl];
		for (var i in rl) {
			if ((traquent.boot ? traquent.boot.user.roles : ["Guest"]).indexOf(rl[i]) != -1)
				return true;
		}
	},
	get_desktop_items: function () {
		// hide based on permission
		var modules_list = $.map(traquent.boot.allowed_modules, function (icon) {
			var m = icon.module_name;
			var type = traquent.modules[m] && traquent.modules[m].type;

			if (traquent.boot.user.allow_modules.indexOf(m) === -1) return null;

			var ret = null;
			if (type === "module") {
				if (traquent.boot.user.allow_modules.indexOf(m) != -1 || traquent.modules[m].is_help)
					ret = m;
			} else if (type === "page") {
				if (traquent.boot.allowed_pages.indexOf(traquent.modules[m].link) != -1) ret = m;
			} else if (type === "list") {
				if (traquent.model.can_read(traquent.modules[m]._doctype)) ret = m;
			} else if (type === "view") {
				ret = m;
			} else if (type === "setup") {
				if (
					traquent.user.has_role("System Manager") ||
					traquent.user.has_role("Administrator")
				)
					ret = m;
			} else {
				ret = m;
			}

			return ret;
		});

		return modules_list;
	},

	is_report_manager: function () {
		return traquent.user.has_role(["Administrator", "System Manager", "Report Manager"]);
	},

	get_formatted_email: function (email) {
		var fullname = traquent.user.full_name(email);

		if (!fullname) {
			return email;
		} else {
			// to quote or to not
			var quote = "";

			// only if these special characters are found
			// why? To make the output same as that in python!
			if (fullname.search(/[\[\]\\()<>@,:;".]/) !== -1) {
				quote = '"';
			}

			return repl("%(quote)s%(fullname)s%(quote)s <%(email)s>", {
				fullname: fullname,
				email: email,
				quote: quote,
			});
		}
	},

	get_emails: () => {
		return Object.keys(traquent.boot.user_info).map((key) => traquent.boot.user_info[key].email);
	},

	/* Normally traquent.user is an object
	 * having properties and methods.
	 * But in the following case
	 *
	 * if (traquent.user === 'Administrator')
	 *
	 * traquent.user will cast to a string
	 * returning traquent.user.name
	 */
	toString: function () {
		return this.name;
	},
});

traquent.session_alive = true;
$(document).bind("mousemove", function () {
	if (traquent.session_alive === false) {
		$(document).trigger("session_alive");
	}
	traquent.session_alive = true;
	if (traquent.session_alive_timeout) clearTimeout(traquent.session_alive_timeout);
	traquent.session_alive_timeout = setTimeout("traquent.session_alive=false;", 30000);
});
