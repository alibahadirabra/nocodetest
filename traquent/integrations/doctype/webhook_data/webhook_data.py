# Copyright (c) 2017, traquent Technologies and contributors
# License: MIT. See LICENSE

# import traquent
from traquent.model.document import Document


class WebhookData(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		fieldname: DF.Literal[None]
		key: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
	# end: auto-generated types

	pass