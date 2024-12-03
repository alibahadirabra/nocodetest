// Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

traquent.provide("traquent.help");

traquent.help.youtube_id = {};

traquent.help.has_help = function (doctype) {
	return traquent.help.youtube_id[doctype];
};

traquent.help.show = function (doctype) {
	if (traquent.help.youtube_id[doctype]) {
		traquent.help.show_video(traquent.help.youtube_id[doctype]);
	}
};

traquent.help.show_video = function (youtube_id, title) {
	if (traquent.utils.is_url(youtube_id)) {
		const expression =
			'(?:youtube.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu.be/)([^"&?\\s]{11})';
		youtube_id = youtube_id.match(expression)[1];
	}

	// (traquent.help_feedback_link || "")
	let dialog = new traquent.ui.Dialog({
		title: title || __("Help"),
		size: "large",
	});

	let video = $(
		`<div class="video-player" data-plyr-provider="youtube" data-plyr-embed-id="${youtube_id}"></div>`
	);
	video.appendTo(dialog.body);

	dialog.show();
	dialog.$wrapper.addClass("video-modal");

	let plyr;
	traquent.utils.load_video_player().then(() => {
		plyr = new traquent.Plyr(video[0], {
			hideControls: true,
			resetOnEnd: true,
		});
	});

	dialog.onhide = () => {
		plyr?.destroy();
	};
};

$("body").on("click", "a.help-link", function () {
	var doctype = $(this).attr("data-doctype");
	doctype && traquent.help.show(doctype);
});
