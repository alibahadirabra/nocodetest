# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent
import traquent.www.list
from traquent import _

no_cache = 1


def get_context(context):
	if traquent.session.user == "Guest":
		traquent.throw(_("You need to be logged in to access this page"), traquent.PermissionError)

	context.current_user = traquent.get_doc("User", traquent.session.user)
	context.show_sidebar = False
