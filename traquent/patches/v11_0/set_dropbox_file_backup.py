import traquent
from traquent.utils import cint


def execute():
	traquent.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(traquent.db.get_single_value("Dropbox Settings", "enabled"))
	if check_dropbox_enabled == 1:
		traquent.db.set_single_value("Dropbox Settings", "file_backup", 1)
