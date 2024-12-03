import traquent


def execute():
	traquent.delete_doc_if_exists("DocType", "Web View")
	traquent.delete_doc_if_exists("DocType", "Web View Component")
	traquent.delete_doc_if_exists("DocType", "CSS Class")
