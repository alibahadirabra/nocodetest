import traquent


def execute():
	traquent.reload_doc("core", "doctype", "domain")
	traquent.reload_doc("core", "doctype", "has_domain")
	active_domains = traquent.get_active_domains()
	all_domains = traquent.get_all("Domain")

	for d in all_domains:
		if d.name not in active_domains:
			inactive_domain = traquent.get_doc("Domain", d.name)
			inactive_domain.setup_data()
			inactive_domain.remove_custom_field()
