import traquent

base_template_path = "www/robots.txt"


def get_context(context):
	robots_txt = (
		traquent.db.get_single_value("Website Settings", "robots_txt")
		or (traquent.local.conf.robots_txt and traquent.read_file(traquent.local.conf.robots_txt))
		or ""
	)

	return {"robots_txt": robots_txt}
