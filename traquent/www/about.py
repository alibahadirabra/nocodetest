# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import traquent

sitemap = 1


def get_context(context):
	context.doc = traquent.get_cached_doc("About Us Settings")

	return context
