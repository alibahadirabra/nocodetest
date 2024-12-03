import traquent
from traquent.model.rename_doc import rename_doc


def execute():
	if traquent.db.exists("DocType", "Client Script"):
		return

	traquent.flags.ignore_route_conflict_validation = True
	rename_doc("DocType", "Custom Script", "Client Script")
	traquent.flags.ignore_route_conflict_validation = False

	traquent.reload_doctype("Client Script", force=True)
