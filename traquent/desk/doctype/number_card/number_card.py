# Copyright (c) 2020, traquent Technologies and contributors
# License: MIT. See LICENSE

import traquent
from traquent import _
from traquent.boot import get_allowed_report_names
from traquent.model.document import Document
from traquent.model.naming import append_number_if_name_exists
from traquent.modules.export_file import export_to_files
from traquent.query_builder import Criterion
from traquent.query_builder.utils import DocType
from traquent.utils import cint, flt
from traquent.utils.modules import get_modules_from_all_apps_for_user


class NumberCard(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from traquent.types import DF

		aggregate_function_based_on: DF.Literal[None]
		color: DF.Color | None
		document_type: DF.Link | None
		dynamic_filters_json: DF.Code | None
		filters_config: DF.Code | None
		filters_json: DF.Code | None
		function: DF.Literal["Count", "Sum", "Average", "Minimum", "Maximum"]
		is_public: DF.Check
		is_standard: DF.Check
		label: DF.Data
		method: DF.Data | None
		module: DF.Link | None
		parent_document_type: DF.Link | None
		report_field: DF.Literal[None]
		report_function: DF.Literal["Sum", "Average", "Minimum", "Maximum"]
		report_name: DF.Link | None
		show_percentage_stats: DF.Check
		stats_time_interval: DF.Literal["Daily", "Weekly", "Monthly", "Yearly"]
		type: DF.Literal["Document Type", "Report", "Custom"]
	# end: auto-generated types

	def autoname(self):
		if not self.name:
			self.name = self.label

		if traquent.db.exists("Number Card", self.name):
			self.name = append_number_if_name_exists("Number Card", self.name)

	def validate(self):
		if self.type == "Document Type":
			if not (self.document_type and self.function):
				traquent.throw(_("Document Type and Function are required to create a number card"))

			if self.function != "Count" and not self.aggregate_function_based_on:
				traquent.throw(_("Aggregate Field is required to create a number card"))

			if traquent.get_meta(self.document_type).istable and not self.parent_document_type:
				traquent.throw(_("Parent Document Type is required to create a number card"))

		elif self.type == "Report":
			if not (self.report_name and self.report_field and self.function):
				traquent.throw(_("Report Name, Report Field and Fucntion are required to create a number card"))

		elif self.type == "Custom":
			if not self.method:
				traquent.throw(_("Method is required to create a number card"))

	def on_update(self):
		if traquent.conf.developer_mode and self.is_standard:
			export_to_files(record_list=[["Number Card", self.name]], record_module=self.module)


def get_permission_query_conditions(user=None):
	if not user:
		user = traquent.session.user

	if user == "Administrator":
		return

	roles = traquent.get_roles(user)
	if "System Manager" in roles:
		return None

	doctype_condition = False
	module_condition = False

	allowed_doctypes = [traquent.db.escape(doctype) for doctype in traquent.permissions.get_doctypes_with_read()]
	allowed_modules = [
		traquent.db.escape(module.get("module_name")) for module in get_modules_from_all_apps_for_user()
	]

	if allowed_doctypes:
		doctype_condition = "`tabNumber Card`.`document_type` in ({allowed_doctypes})".format(
			allowed_doctypes=",".join(allowed_doctypes)
		)
	if allowed_modules:
		module_condition = """`tabNumber Card`.`module` in ({allowed_modules})
			or `tabNumber Card`.`module` is NULL""".format(allowed_modules=",".join(allowed_modules))

	return f"""
		{doctype_condition}
		and
		{module_condition}
	"""


def has_permission(doc, ptype, user):
	roles = traquent.get_roles(user)
	if "System Manager" in roles:
		return True

	if doc.type == "Report":
		if doc.report_name in get_allowed_report_names():
			return True
	else:
		allowed_doctypes = tuple(traquent.permissions.get_doctypes_with_read())
		if doc.document_type in allowed_doctypes:
			return True

	return False


frappe.whitelist()
def get_result(doc, filters, to_date=None):
	doc = traquent.parse_json(doc)
	fields = []
	sql_function_map = {
		"Count": "count",
		"Sum": "sum",
		"Average": "avg",
		"Minimum": "min",
		"Maximum": "max",
	}

	function = sql_function_map[doc.function]

	if function == "count":
		fields = [f"{function}(*) as result"]
	else:
		fields = [f"{function}({doc.aggregate_function_based_on}) as result"]

	if not filters:
		filters = []
	elif isinstance(filters, str):
		filters = traquent.parse_json(filters)

	if to_date:
		filters.append([doc.document_type, "creation", "<", to_date])

	res = traquent.get_list(
		doc.document_type, fields=fields, filters=filters, parent_doctype=doc.parent_document_type
	)
	number = res[0]["result"] if res else 0

	return flt(number)


frappe.whitelist()
def get_percentage_difference(doc, filters, result):
	doc = traquent.parse_json(doc)
	result = traquent.parse_json(result)

	doc = traquent.get_doc("Number Card", doc.name)

	if not doc.get("show_percentage_stats"):
		return

	previous_result = calculate_previous_result(doc, filters)
	if previous_result == 0:
		return None
	else:
		if result == previous_result:
			return 0
		else:
			return ((result / previous_result) - 1) * 100.0


def calculate_previous_result(doc, filters):
	from traquent.utils import add_to_date

	current_date = traquent.utils.now()
	if doc.stats_time_interval == "Daily":
		previous_date = add_to_date(current_date, days=-1)
	elif doc.stats_time_interval == "Weekly":
		previous_date = add_to_date(current_date, weeks=-1)
	elif doc.stats_time_interval == "Monthly":
		previous_date = add_to_date(current_date, months=-1)
	else:
		previous_date = add_to_date(current_date, years=-1)

	return get_result(doc, filters, previous_date)


frappe.whitelist()
def create_number_card(args):
	args = traquent.parse_json(args)
	doc = traquent.new_doc("Number Card")

	doc.update(args)
	doc.insert(ignore_permissions=True)
	return doc


frappe.whitelist()
frappe.validate_and_sanitize_search_inputs
def get_cards_for_user(doctype, txt, searchfield, start, page_len, filters):
	meta = traquent.get_meta(doctype)
	searchfields = meta.get_search_fields()
	search_conditions = []

	if not traquent.db.exists("DocType", doctype):
		return

	numberCard = DocType("Number Card")

	if txt:
		search_conditions = [numberCard[field].like(f"%{txt}%") for field in searchfields]

	condition_query = traquent.qb.get_query(
		doctype,
		filters=filters,
		validate_filters=True,
	)

	return (
		condition_query.select(numberCard.name, numberCard.label, numberCard.document_type)
		.where((numberCard.owner == traquent.session.user) | (numberCard.is_public == 1))
		.where(Criterion.any(search_conditions))
	).run()


frappe.whitelist()
def create_report_number_card(args):
	card = create_number_card(args)
	args = traquent.parse_json(args)
	args.name = card.name
	if args.dashboard:
		add_card_to_dashboard(traquent.as_json(args))


frappe.whitelist()
def add_card_to_dashboard(args):
	args = traquent.parse_json(args)

	dashboard = traquent.get_doc("Dashboard", args.dashboard)
	dashboard_link = traquent.new_doc("Number Card Link")
	dashboard_link.card = args.name

	if args.set_standard and dashboard.is_standard:
		card = traquent.get_doc("Number Card", dashboard_link.card)
		card.is_standard = 1
		card.module = dashboard.module
		card.save()

	dashboard.append("cards", dashboard_link)
	dashboard.save()
