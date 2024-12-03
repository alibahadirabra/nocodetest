# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE
import traquent
from traquent import _

no_cache = 1


def get_context(context):
	if traquent.flags.in_migrate:
		return

	allow_traceback = traquent.get_system_settings("allow_error_traceback") if traquent.db else False

	context.error_title = context.error_title or _("Uncaught Server Exception")
	context.error_message = context.error_message or _("There was an error building this page")

	return {
		"error": traquent.get_traceback().replace("<", "&lt;").replace(">", "&gt;") if allow_traceback else ""
	}
