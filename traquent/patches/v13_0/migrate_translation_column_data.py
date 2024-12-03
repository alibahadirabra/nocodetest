import traquent


def execute():
	traquent.reload_doctype("Translation")
	traquent.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
