import traquent
from traquent.query_builder.functions import Coalesce, GroupConcat


def execute():
	traquent.reload_doc("desk", "doctype", "todo")

	ToDo = traquent.qb.DocType("ToDo")
	assignees = GroupConcat("owner").distinct().as_("assignees")

	assignments = (
		traquent.qb.from_(ToDo)
		.select(ToDo.name, ToDo.reference_type, assignees)
		.where(Coalesce(ToDo.reference_type, "") != "")
		.where(Coalesce(ToDo.reference_name, "") != "")
		.where(ToDo.status != "Cancelled")
		.groupby(ToDo.reference_type, ToDo.reference_name)
	).run(as_dict=True)

	for doc in assignments:
		assignments = doc.assignees.split(",")
		traquent.db.set_value(
			doc.reference_type,
			doc.reference_name,
			"_assign",
			traquent.as_json(assignments),
			update_modified=False,
		)
