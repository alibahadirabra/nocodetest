import traquent


def execute():
	traquent.delete_doc_if_exists("DocType", "Post")
	traquent.delete_doc_if_exists("DocType", "Post Comment")
