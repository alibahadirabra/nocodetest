import traquent


def execute():
	traquent.reload_doc("website", "doctype", "web_page_view", force=True)
	site_url = traquent.utils.get_site_url(traquent.local.site)
	traquent.db.sql(f"""UPDATE `tabWeb Page View` set is_unique=1 where referrer LIKE '%{site_url}%'""")
