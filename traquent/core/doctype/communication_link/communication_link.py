# Copyright (c) 2019, traquent Technologies and contributors
# License: MIT. See LICENSE

import traquent
from traquent.model.document import Document


class CommunicationLink(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		link_doctype: DF.Link
		link_name: DF.DynamicLink
		link_title: DF.ReadOnly | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass


def on_doctype_update():
	traquent.db.add_index("Communication Link", ["link_doctype", "link_name"])