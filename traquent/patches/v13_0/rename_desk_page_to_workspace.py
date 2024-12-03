import traquent
from traquent.model.rename_doc import rename_doc


def execute():
	if traquent.db.exists("DocType", "Desk Page"):
		if traquent.db.exists("DocType", "Workspace"):
			# this patch was not added initially, so this page might still exist
			traquent.delete_doc("DocType", "Desk Page")
		else:
			traquent.flags.ignore_route_conflict_validation = True
			rename_doc("DocType", "Desk Page", "Workspace")
			traquent.flags.ignore_route_conflict_validation = False

	rename_doc("DocType", "Desk Chart", "Workspace Chart", ignore_if_exists=True)
	rename_doc("DocType", "Desk Shortcut", "Workspace Shortcut", ignore_if_exists=True)
	rename_doc("DocType", "Desk Link", "Workspace Link", ignore_if_exists=True)

	traquent.reload_doc("desk", "doctype", "workspace", force=True)
	traquent.reload_doc("desk", "doctype", "workspace_link", force=True)
	traquent.reload_doc("desk", "doctype", "workspace_chart", force=True)
	traquent.reload_doc("desk", "doctype", "workspace_shortcut", force=True)
