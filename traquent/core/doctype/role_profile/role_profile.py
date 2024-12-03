# Copyright (c) 2017, traquent Technologies and contributors
# License: MIT. See LICENSE

from collections import defaultdict

import traquent
from traquent.model.document import Document


class RoleProfile(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.core.doctype.has_role.has_role import HasRole
		from traquent.types import DF

		role_profile: DF.Data
		roles: DF.Table[HasRole]
	# end: auto-generated types

	def autoname(self):
		"""set name as Role Profile name"""
		self.name = self.role_profile

	def on_update(self):
		self.queue_action(
			"update_all_users",
			now=traquent.flags.in_test or traquent.flags.in_install,
			enqueue_after_commit=True,
			queue="long",
		)

	def update_all_users(self):
		"""Changes in role_profile reflected across all its user"""
		users = traquent.get_all("User Role Profile", filters={"role_profile": self.name}, pluck="parent")
		for user in users:
			user = traquent.get_doc("User", user)
			user.save()  # resaving syncs roles

	def get_permission_log_options(self, event=None):
		return {"fields": ["roles"]}
