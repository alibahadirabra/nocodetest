// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

// for translation
traquent._ = function (txt, replace, context = null) {
	if (!txt) return txt;
	if (typeof txt != "string") return txt;

	let translated_text = "";

	let key = txt; // txt.replace(/\n/g, "");
	if (context) {
		translated_text = traquent._messages[`${key}:${context}`];
	}

	if (!translated_text) {
		translated_text = traquent._messages[key] || txt;
	}

	if (replace && typeof replace === "object") {
		translated_text = $.format(translated_text, replace);
	}
	return translated_text;
};

window.__ = traquent._;

traquent.get_languages = function () {
	if (!traquent.languages) {
		traquent.languages = [];
		$.each(traquent.boot.lang_dict, function (lang, value) {
			traquent.languages.push({ label: lang, value: value });
		});
		traquent.languages = traquent.languages.sort(function (a, b) {
			return a.value < b.value ? -1 : 1;
		});
	}
	return traquent.languages;
};
