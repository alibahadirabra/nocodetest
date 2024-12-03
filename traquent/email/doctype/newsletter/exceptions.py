# Copyright (c) 2021, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See LICENSE

from traquent.exceptions import ValidationError


class NewsletterAlreadySentError(ValidationError):
	pass


class NoRecipientFoundError(ValidationError):
	pass


class NewsletterNotSavedError(ValidationError):
	pass
