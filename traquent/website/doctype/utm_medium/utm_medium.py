# Copyright (c) 2024, traquent Technologies and contributors
# For license information, please see license.txt

import traquent
from traquent.model.document import Document


class UTMMedium(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		description: DF.SmallText | None
		slug: DF.Data | None
	# end: auto-generated types

	def before_save(self):
		if self.slug:
			self.slug = traquent.utils.slug(self.slug)