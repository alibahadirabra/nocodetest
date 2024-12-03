import traquent


def execute():
	for dt in traquent.get_all("Workflow", fields=["name", "document_type", "workflow_state_field"]):
		fieldname = traquent.db.get_value(
			"Custom Field", filters={"dt": dt.document_type, "fieldname": dt.workflow_state_field}
		)

		if fieldname:
			custom_field = traquent.get_doc("Custom Field", fieldname)
			custom_field.no_copy = 1
			custom_field.save()
