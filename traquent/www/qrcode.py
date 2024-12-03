# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

from urllib.parse import parse_qsl

import traquent
from traquent import _
from traquent.twofactor import get_qr_svg_code


def get_context(context):
	context.no_cache = 1
	context.qr_code_user, context.qrcode_svg = get_user_svg_from_cache()


def get_query_key():
	"""Return query string arg."""
	query_string = traquent.local.request.query_string
	query = dict(parse_qsl(query_string))
	query = {key.decode(): val.decode() for key, val in query.items()}
	if "k" not in list(query):
		traquent.throw(_("Not Permitted"), traquent.PermissionError)
	query = (query["k"]).strip()
	if False in [i.isalpha() or i.isdigit() for i in query]:
		traquent.throw(_("Not Permitted"), traquent.PermissionError)
	return query


def get_user_svg_from_cache():
	"""Get User and SVG code from cache."""
	key = get_query_key()
	totp_uri = traquent.cache.get_value(f"{key}_uri")
	user = traquent.cache.get_value(f"{key}_user")
	if not totp_uri or not user:
		traquent.throw(_("Page has expired!"), traquent.PermissionError)
	if not traquent.db.exists("User", user):
		traquent.throw(_("Not Permitted"), traquent.PermissionError)
	user = traquent.get_doc("User", user)
	svg = get_qr_svg_code(totp_uri)
	return (user, svg.decode())
