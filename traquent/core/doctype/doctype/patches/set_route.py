import traquent
from traquent.desk.utils import slug


def execute():
	for doctype in traquent.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			traquent.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
