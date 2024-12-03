import traquent


def execute():
	Event = traquent.qb.DocType("Event")
	query = (
		traquent.qb.update(Event)
		.set(Event.event_type, "Private")
		.set(Event.status, "Cancelled")
		.where(Event.event_type == "Cancelled")
	)
	query.run()
