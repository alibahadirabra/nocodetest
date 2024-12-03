# Copyright (c) 2023, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import traquent
from traquent.core.doctype.user.user import desk_properties


def execute():
	roles = {role.name: role for role in traquent.get_all("Role", fields=["*"])}

	for user in traquent.get_list("User"):
		user_desk_settings = {}
		for role_name in traquent.get_roles(username=user.name):
			if role := roles.get(role_name):
				for key in desk_properties:
					if role.get(key) is None:
						role[key] = 1
					user_desk_settings[key] = user_desk_settings.get(key) or role.get(key)

		traquent.db.set_value("User", user.name, user_desk_settings)
