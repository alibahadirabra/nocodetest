import traquent


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	traquent.delete_doc("DocType", "Feedback Trigger")
	traquent.delete_doc("DocType", "Feedback Rating")
