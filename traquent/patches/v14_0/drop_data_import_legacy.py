import click

import traquent


def execute():
	doctype = "Data Import Legacy"
	table = traquent.utils.get_table_name(doctype)

	# delete the doctype record to avoid broken links
	traquent.delete_doc("DocType", doctype, force=True)

	# leaving table in database for manual cleanup
	click.secho(
		f"`{doctype}` has been deprecated. The DocType is deleted, but the data still"
		" exists on the database. If this data is worth recovering, you may export it"
		f" using\n\n\tbench --site {traquent.local.site} backup -i '{doctype}'\n\nAfter"
		" this, the table will continue to persist in the database, until you choose"
		" to remove it yourself. If you want to drop the table, you may run\n\n\tbench"
		f" --site {traquent.local.site} execute traquent.db.sql --args \"('DROP TABLE IF"
		f" EXISTS `{table}`', )\"\n",
		fg="yellow",
	)