import traquent


def execute():
	traquent.reload_doc("website", "doctype", "web_page_view", force=True)
	traquent.db.sql("""UPDATE `tabWeb Page View` set path='/' where path=''""")
