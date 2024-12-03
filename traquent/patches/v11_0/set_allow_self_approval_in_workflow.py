import traquent


def execute():
	traquent.reload_doc("workflow", "doctype", "workflow_transition")
	traquent.db.sql("update `tabWorkflow Transition` set allow_self_approval=1")
