# Copyright (c) 2017, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import traquent


frappe.whitelist()
def get_leaderboard_config():
	leaderboard_config = traquent._dict()
	leaderboard_hooks = traquent.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(traquent.get_attr(hook)())

	return leaderboard_config
