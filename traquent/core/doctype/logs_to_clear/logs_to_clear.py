# Copyright (c) 2022, traquent Technologies and contributors
# For license information, please see license.txt

# import traquent
from traquent.model.document import Document


class LogsToClear(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		days: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		ref_doctype: DF.Link
	# end: auto-generated types

	pass
