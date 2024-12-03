import click

import traquent


def execute():
	traquent.delete_doc_if_exists("DocType", "Chat Message")
	traquent.delete_doc_if_exists("DocType", "Chat Message Attachment")
	traquent.delete_doc_if_exists("DocType", "Chat Profile")
	traquent.delete_doc_if_exists("DocType", "Chat Token")
	traquent.delete_doc_if_exists("DocType", "Chat Room User")
	traquent.delete_doc_if_exists("DocType", "Chat Room")
	traquent.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from traquent in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/traquent/chat",
		fg="yellow",
	)
