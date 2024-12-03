import traquent

from ...user.user import desk_properties


def execute():
	for role in traquent.get_all("Role", ["name", "desk_access"]):
		role_doc = traquent.get_doc("Role", role.name)
		for key in desk_properties:
			role_doc.set(key, role_doc.desk_access)
		role_doc.save()
