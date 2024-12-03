# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and contributors
# License: MIT. See LICENSE

import traquent
from traquent import _
from traquent.model.document import Document


class EmailUnsubscribe(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		email: DF.Data
		global_unsubscribe: DF.Check
		reference_doctype: DF.Link | None
		reference_name: DF.DynamicLink | None
	# end: auto-generated types

	def validate(self):
		if not self.global_unsubscribe and not (self.reference_doctype and self.reference_name):
			traquent.throw(_("Reference DocType and Reference Name are required"), traquent.MandatoryError)

		if not self.global_unsubscribe and traquent.db.get_value(self.doctype, self.name, "global_unsubscribe"):
			traquent.throw(_("Delete this record to allow sending to this email address"))

		if self.global_unsubscribe:
			if traquent.get_all(
				"Email Unsubscribe",
				filters={"email": self.email, "global_unsubscribe": 1, "name": ["!=", self.name]},
			):
				traquent.throw(_("{0} already unsubscribed").format(self.email), traquent.DuplicateEntryError)

		else:
			if traquent.get_all(
				"Email Unsubscribe",
				filters={
					"email": self.email,
					"reference_doctype": self.reference_doctype,
					"reference_name": self.reference_name,
					"name": ["!=", self.name],
				},
			):
				traquent.throw(
					_("{0} already unsubscribed for {1} {2}").format(
						self.email, self.reference_doctype, self.reference_name
					),
					traquent.DuplicateEntryError,
				)

	def on_update(self):
		if self.reference_doctype and self.reference_name:
			doc = traquent.get_doc(self.reference_doctype, self.reference_name)
			doc.add_comment("Label", _("Left this conversation"), comment_email=self.email)
