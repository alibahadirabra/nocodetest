import traquent
from traquent.model.rename_doc import rename_doc


def execute():
	if traquent.db.table_exists("Workflow Action") and not traquent.db.table_exists("Workflow Action Master"):
		rename_doc("DocType", "Workflow Action", "Workflow Action Master")
		traquent.reload_doc("workflow", "doctype", "workflow_action_master")
