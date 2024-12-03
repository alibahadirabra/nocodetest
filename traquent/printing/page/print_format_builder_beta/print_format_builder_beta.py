# Copyright (c) 2021, traquent Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import functools

import traquent


@traquent.whitelist()
def get_google_fonts():
	return _get_google_fonts()


@functools.lru_cache
def _get_google_fonts():
	file_path = traquent.get_app_path("traquent", "data", "google_fonts.json")
	return traquent.parse_json(traquent.read_file(file_path))
