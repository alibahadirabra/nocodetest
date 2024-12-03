# Copyright (c) 2022, traquent Technologies and contributors
# For license information, please see license.txt

# import traquent
from traquent.model.document import Document


class WorkspaceQuickList(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		document_type: DF.Link
		label: DF.Data
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		quick_list_filter: DF.Code | None
	# end: auto-generated types

	pass
