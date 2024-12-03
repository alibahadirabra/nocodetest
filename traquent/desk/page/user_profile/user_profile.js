traquent.pages["user-profile"].on_page_load = function (wrapper) {
	traquent.require("user_profile_controller.bundle.js", () => {
		let user_profile = new traquent.ui.UserProfile(wrapper);
		user_profile.show();
	});
};
