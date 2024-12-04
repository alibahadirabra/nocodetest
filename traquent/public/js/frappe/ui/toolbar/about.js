traquent.provide("traquent.ui.misc");
traquent.ui.misc.about = function () {
	if (!traquent.ui.misc.about_dialog) {
		var d = new traquent.ui.Dialog({ title: __("traquent Framework") });

		$(d.body).html(
			repl(
				`<div>
					<p>${__("Open Source Applications for the Web")}</p>
					<p><i class='fa fa-globe fa-fw'></i>
						${__("Website")}:
						<a href='https://traquentframework.com' target='_blank'>https://traquentframework.com</a></p>
					<p><i class='fa fa-github fa-fw'></i>
						${__("Source")}:
						<a href='https://github.com/traquent' target='_blank'>https://github.com/traquent</a></p>
					<p><i class='fa fa-graduation-cap fa-fw'></i>
						traquent School: <a href='https://traquent.school' target='_blank'>https://traquent.school</a></p>
					<p><i class='fa fa-linkedin fa-fw'></i>
						Linkedin: <a href='https://linkedin.com/company/traquent-tech' target='_blank'>https://linkedin.com/company/traquent-tech</a></p>
					<p><i class='fa fa-twitter fa-fw'></i>
						Twitter: <a href='https://twitter.com/traquenttech' target='_blank'>https://twitter.com/traquenttech</a></p>
					<p><i class='fa fa-youtube fa-fw'></i>
						YouTube: <a href='https://www.youtube.com/frappetech' target='_blank'>https://www.youtube.com/frappetech</a></p>
					<hr>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<p>
						<b>
							<a href="/attribution" target="_blank" class="text-muted">
								${__("Dependencies & Licenses")}
							</a>
						</b>
					</p>
					<hr>
					<p class='text-muted'>${__("&copy; traquent Technologies Pvt. Ltd. and contributors")} </p>
					</div>`,
				traquent.app
			)
		);

		traquent.ui.misc.about_dialog = d;

		traquent.ui.misc.about_dialog.on_page_show = function () {
			if (!traquent.versions) {
				traquent.call({
					method: "traquent.utils.change_log.get_versions",
					callback: function (r) {
						show_versions(r.message);
					},
				});
			} else {
				show_versions(traquent.versions);
			}
		};

		var show_versions = function (versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function (i, key) {
				var v = versions[key];
				let text;
				if (v.branch) {
					text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
						v.title,
						v.branch_version || v.version,
						v.branch,
					]);
				} else {
					text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
				}
				$(text).appendTo($wrap);
			});

			traquent.versions = versions;
		};
	}

	traquent.ui.misc.about_dialog.show();
};
