# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent
from traquent.utils import strip_html_tags
from traquent.utils.html_utils import clean_html

no_cache = 1


def get_context(context):
	message_context = traquent._dict()
	if hasattr(traquent.local, "message"):
		message_context["header"] = traquent.local.message_title
		message_context["title"] = strip_html_tags(traquent.local.message_title)
		message_context["message"] = traquent.local.message
		if hasattr(traquent.local, "message_success"):
			message_context["success"] = traquent.local.message_success

	elif traquent.local.form_dict.id:
		message_id = traquent.local.form_dict.id
		key = f"message_id:{message_id}"
		message = traquent.cache.get_value(key, expires=True)
		if message:
			message_context.update(message.get("context", {}))
			if message.get("http_status_code"):
				traquent.local.response["http_status_code"] = message["http_status_code"]

	if not message_context.title:
		message_context.title = clean_html(traquent.form_dict.title)

	if not message_context.message:
		message_context.message = clean_html(traquent.form_dict.message)

	return message_context
