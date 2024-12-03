import json

from werkzeug.routing import Rule

import traquent
from traquent import _
from traquent.utils.data import sbool


def document_list(doctype: str):
	if traquent.form_dict.get("fields"):
		traquent.form_dict["fields"] = json.loads(traquent.form_dict["fields"])

	# set limit of records for traquent.get_list
	traquent.form_dict.setdefault(
		"limit_page_length",
		traquent.form_dict.limit or traquent.form_dict.limit_page_length or 20,
	)

	# convert strings to native types - only as_dict and debug accept bool
	for param in ["as_dict", "debug"]:
		param_val = traquent.form_dict.get(param)
		if param_val is not None:
			traquent.form_dict[param] = sbool(param_val)

	# evaluate traquent.get_list
	return traquent.call(traquent.client.get_list, doctype, **traquent.form_dict)


def handle_rpc_call(method: str):
	import traquent.handler

	method = method.split("/")[0]  # for backward compatiblity

	traquent.form_dict.cmd = method
	return traquent.handler.handle()


def create_doc(doctype: str):
	data = get_request_form_data()
	data.pop("doctype", None)
	return traquent.new_doc(doctype, **data).insert()


def update_doc(doctype: str, name: str):
	data = get_request_form_data()

	doc = traquent.get_doc(doctype, name, for_update=True)
	if "flags" in data:
		del data["flags"]

	doc.update(data)
	doc.save()

	# check for child table doctype
	if doc.get("parenttype"):
		traquent.get_doc(doc.parenttype, doc.parent).save()

	return doc


def delete_doc(doctype: str, name: str):
	# TODO: child doc handling
	traquent.delete_doc(doctype, name, ignore_missing=False)
	traquent.response.http_status_code = 202
	return "ok"


def read_doc(doctype: str, name: str):
	# Backward compatiblity
	if "run_method" in traquent.form_dict:
		return execute_doc_method(doctype, name)

	doc = traquent.get_doc(doctype, name)
	if not doc.has_permission("read"):
		raise traquent.PermissionError
	doc.apply_fieldlevel_read_permissions()
	return doc


def execute_doc_method(doctype: str, name: str, method: str | None = None):
	method = method or traquent.form_dict.pop("run_method")
	doc = traquent.get_doc(doctype, name)
	doc.is_whitelisted(method)

	if traquent.request.method == "GET":
		if not doc.has_permission("read"):
			traquent.throw(_("Not permitted"), traquent.PermissionError)
		return doc.run_method(method, **traquent.form_dict)

	elif traquent.request.method == "POST":
		if not doc.has_permission("write"):
			traquent.throw(_("Not permitted"), traquent.PermissionError)

		return doc.run_method(method, **traquent.form_dict)


def get_request_form_data():
	if traquent.form_dict.data is None:
		data = traquent.safe_decode(traquent.request.get_data())
	else:
		data = traquent.form_dict.data

	try:
		return traquent.parse_json(data)
	except ValueError:
		return traquent.form_dict


url_rules = [
	Rule("/method/<path:method>", endpoint=handle_rpc_call),
	Rule("/resource/<doctype>", methods=["GET"], endpoint=document_list),
	Rule("/resource/<doctype>", methods=["POST"], endpoint=create_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["GET"], endpoint=read_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["PUT"], endpoint=update_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["DELETE"], endpoint=delete_doc),
	Rule("/resource/<doctype>/<path:name>/", methods=["POST"], endpoint=execute_doc_method),
]
