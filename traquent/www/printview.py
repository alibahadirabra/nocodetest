# Copyright (c) 2015, traquent Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import copy
import json
import os
import re
from typing import TYPE_CHECKING, Optional, TypedDict

import traquent
from traquent import _, cstr, get_module_path
from traquent.core.doctype.access_log.access_log import make_access_log
from traquent.core.doctype.document_share_key.document_share_key import is_expired
from traquent.utils import cint, escape_html, strip_html
from traquent.utils.jinja_globals import is_rtl

if TYPE_CHECKING:
	from traquent.core.doctype.docfield.docfield import DocField
	from traquent.model.document import Document
	from traquent.model.meta import Meta
	from traquent.printing.doctype.print_format.print_format import PrintFormat
	from traquent.printing.doctype.print_settings.print_settings import PrintSettings

no_cache = 1

standard_format = "templates/print_formats/standard.html"


class PrintContext(TypedDict):
	body: str
	print_style: str
	comment: str
	title: str
	lang: str
	layout_direction: str
	doctype: str
	name: str
	key: str


def get_context(context) -> PrintContext:
	"""Build context for print"""
	if not ((traquent.form_dict.doctype and traquent.form_dict.name) or traquent.form_dict.doc):
		return {
			"body": f"""
				<h1>Error</h1>
				<p>Parameters doctype and name required</p>
				<pre>{escape_html(traquent.as_json(traquent.form_dict, indent=2))}</pre>
				"""
		}

	if traquent.form_dict.doc:
		doc = traquent.form_dict.doc
	else:
		doc = traquent.get_doc(traquent.form_dict.doctype, traquent.form_dict.name)

	set_link_titles(doc)

	settings = traquent.parse_json(traquent.form_dict.settings)

	letterhead = traquent.form_dict.letterhead or None

	meta = traquent.get_meta(doc.doctype)

	print_format = get_print_format_doc(None, meta=meta)

	make_access_log(
		doctype=traquent.form_dict.doctype, document=traquent.form_dict.name, file_type="PDF", method="Print"
	)

	body = get_rendered_template(
		doc,
		print_format=print_format,
		meta=meta,
		trigger_print=traquent.form_dict.trigger_print,
		no_letterhead=traquent.form_dict.no_letterhead,
		letterhead=letterhead,
		settings=settings,
	)
	print_style = get_print_style(traquent.form_dict.style, print_format)

	return {
		"body": body,
		"print_style": print_style,
		"comment": traquent.session.user,
		"title": traquent.utils.strip_html(cstr(doc.get_title() or doc.name)),
		"lang": traquent.local.lang,
		"layout_direction": "rtl" if is_rtl() else "ltr",
		"doctype": traquent.form_dict.doctype,
		"name": traquent.form_dict.name,
		"key": traquent.form_dict.get("key"),
	}


def get_print_format_doc(print_format_name: str, meta: "Meta") -> Optional["PrintFormat"]:
	"""Return print format document."""
	if not print_format_name:
		print_format_name = traquent.form_dict.format or meta.default_print_format or "Standard"

	if print_format_name == "Standard":
		return None
	else:
		try:
			return traquent.get_doc("Print Format", print_format_name)
		except traquent.DoesNotExistError:
			# if old name, return standard!
			return None


def get_rendered_template(
	doc: "Document",
	print_format: Optional["PrintFormat"] = None,
	meta: "Meta" = None,
	no_letterhead: bool | None = None,
	letterhead: str | None = None,
	trigger_print: bool = False,
	settings: dict | None = None,
) -> str:
	print_settings = traquent.get_single("Print Settings").as_dict()
	print_settings.update(settings or {})

	if isinstance(no_letterhead, str):
		no_letterhead = cint(no_letterhead)

	elif no_letterhead is None:
		no_letterhead = not cint(print_settings.with_letterhead)

	doc.flags.in_print = True
	doc.flags.print_settings = print_settings

	if not traquent.flags.ignore_print_permissions:
		validate_print_permission(doc)

	if doc.meta.is_submittable:
		if doc.docstatus.is_draft() and not cint(print_settings.allow_print_for_draft):
			traquent.throw(_("Not allowed to print draft documents"), traquent.PermissionError)

		if doc.docstatus.is_cancelled() and not cint(print_settings.allow_print_for_cancelled):
			traquent.throw(_("Not allowed to print cancelled documents"), traquent.PermissionError)

	doc.run_method("before_print", print_settings)

	if not hasattr(doc, "print_heading"):
		doc.print_heading = None
	if not hasattr(doc, "sub_heading"):
		doc.sub_heading = None

	if not meta:
		meta = traquent.get_meta(doc.doctype)

	jenv = traquent.get_jenv()
	format_data, format_data_map = [], {}

	# determine template
	if print_format:
		doc.print_section_headings = print_format.show_section_headings
		doc.print_line_breaks = print_format.line_breaks
		doc.align_labels_right = print_format.align_labels_right
		doc.absolute_value = print_format.absolute_value

		def get_template_from_string():
			return jenv.from_string(get_print_format(doc.doctype, print_format))

		template = None
		if hook_func := traquent.get_hooks("get_print_format_template"):
			template = traquent.get_attr(hook_func[-1])(jenv=jenv, print_format=print_format)

		if template:
			pass
		elif print_format.custom_format:
			template = get_template_from_string()

		elif print_format.format_data:
			# set format data
			format_data = json.loads(print_format.format_data)
			for df in format_data:
				format_data_map[df.get("fieldname")] = df
				if "visible_columns" in df:
					for _df in df.get("visible_columns"):
						format_data_map[_df.get("fieldname")] = _df

			doc.format_data_map = format_data_map

			template = "standard"

		elif print_format.standard == "Yes":
			template = get_template_from_string()

		else:
			# fallback
			template = "standard"

	else:
		template = "standard"

	if template == "standard":
		template = jenv.get_template(standard_format)

	letter_head = traquent._dict(get_letter_head(doc, no_letterhead, letterhead) or {})

	if letter_head.content:
		letter_head.content = traquent.utils.jinja.render_template(letter_head.content, {"doc": doc.as_dict()})
		if letter_head.header_script:
			letter_head.content += f"""
				<script>
					{ letter_head.header_script }
				</script>
			"""

	if letter_head.footer:
		letter_head.footer = traquent.utils.jinja.render_template(letter_head.footer, {"doc": doc.as_dict()})
		if letter_head.footer_script:
			letter_head.footer += f"""
				<script>
					{ letter_head.footer_script }
				</script>
			"""

	convert_markdown(doc)

	args = {}
	# extract `print_heading_template` from the first field and remove it
	if format_data and format_data[0].get("fieldname") == "print_heading_template":
		args["print_heading_template"] = format_data.pop(0).get("options")

	args.update(
		{
			"doc": doc,
			"meta": traquent.get_meta(doc.doctype),
			"layout": make_layout(doc, meta, format_data),
			"no_letterhead": no_letterhead,
			"trigger_print": cint(trigger_print),
			"letter_head": letter_head.content,
			"footer": letter_head.footer,
			"print_settings": print_settings,
		}
	)
	hook_func = traquent.get_hooks("pdf_body_html")
	html = traquent.get_attr(hook_func[-1])(jenv=jenv, template=template, print_format=print_format, args=args)

	if cint(trigger_print):
		html += trigger_print_script

	return html


def set_link_titles(doc: "Document") -> None:
	# Adds name with title of link field doctype to __link_titles
	if not doc.get("__link_titles"):
		setattr(doc, "__link_titles", {})

	meta = traquent.get_meta(doc.doctype)
	set_title_values_for_link_and_dynamic_link_fields(meta, doc)
	set_title_values_for_table_and_multiselect_fields(meta, doc)


def set_title_values_for_link_and_dynamic_link_fields(
	meta: "Meta", doc: "Document", parent_doc: Optional["Document"] = None
) -> None:
	if parent_doc and not parent_doc.get("__link_titles"):
		setattr(parent_doc, "__link_titles", {})
	elif doc and not doc.get("__link_titles"):
		setattr(doc, "__link_titles", {})

	for field in meta.get_link_fields() + meta.get_dynamic_link_fields():
		if not doc.get(field.fieldname):
			continue

		# If link field, then get doctype from options
		# If dynamic link field, then get doctype from dependent field
		doctype = field.options if field.fieldtype == "Link" else doc.get(field.options)

		meta = traquent.get_meta(doctype)
		if not meta or not meta.title_field or not meta.show_title_field_in_link:
			continue

		link_title = traquent.get_cached_value(doctype, doc.get(field.fieldname), meta.title_field)
		if parent_doc:
			parent_doc.__link_titles[f"{doctype}::{doc.get(field.fieldname)}"] = link_title
		elif doc:
			doc.__link_titles[f"{doctype}::{doc.get(field.fieldname)}"] = link_title


def set_title_values_for_table_and_multiselect_fields(meta: "Meta", doc: "Document") -> None:
	for field in meta.get_table_fields():
		if not doc.get(field.fieldname):
			continue

		_meta = traquent.get_meta(field.options)
		for value in doc.get(field.fieldname):
			set_title_values_for_link_and_dynamic_link_fields(_meta, value, doc)


def convert_markdown(doc: "Document") -> None:
	"""Convert text field values to markdown if necessary."""
	for field in doc.meta.fields:
		if field.fieldtype == "Text Editor":
			value = doc.get(field.fieldname)
			if value and "<!-- markdown -->" in value:
				doc.set(field.fieldname, traquent.utils.md_to_html(value))


@traquent.whitelist()
def get_html_and_style(
	doc: str,
	name: str | None = None,
	print_format: str | None = None,
	no_letterhead: bool | None = None,
	letterhead: str | None = None,
	trigger_print: bool = False,
	style: str | None = None,
	settings: str | None = None,
) -> dict[str, str]:
	"""Return `html` and `style` of print format, used in PDF etc."""

	if isinstance(name, str):
		document = traquent.get_doc(doc, name)
	else:
		document = traquent.get_doc(json.loads(doc))

	document.check_permission()

	print_format = get_print_format_doc(print_format, meta=document.meta)
	set_link_titles(document)

	try:
		html = get_rendered_template(
			doc=document,
			print_format=print_format,
			meta=document.meta,
			no_letterhead=no_letterhead,
			letterhead=letterhead,
			trigger_print=trigger_print,
			settings=traquent.parse_json(settings),
		)
	except traquent.TemplateNotFoundError:
		traquent.clear_last_message()
		html = None

	return {"html": html, "style": get_print_style(style=style, print_format=print_format)}


@traquent.whitelist()
def get_rendered_raw_commands(doc: str, name: str | None = None, print_format: str | None = None) -> dict:
	"""Return Rendered Raw Commands of print format, used to send directly to printer."""

	if isinstance(name, str):
		document = traquent.get_doc(doc, name)
	else:
		document = traquent.get_doc(json.loads(doc))

	document.check_permission()

	print_format = get_print_format_doc(print_format, meta=document.meta)

	if not print_format or (print_format and not print_format.raw_printing):
		traquent.throw(
			_("{0} is not a raw printing format.").format(print_format), traquent.TemplateNotFoundError
		)

	return {
		"raw_commands": get_rendered_template(doc=document, print_format=print_format, meta=document.meta)
	}


def validate_print_permission(doc: "Document") -> None:
	for ptype in ("read", "print"):
		if traquent.has_permission(doc.doctype, ptype, doc) or traquent.has_website_permission(doc):
			return

	key = traquent.form_dict.key
	if key and isinstance(key, str):
		validate_key(key, doc)
	else:
		raise traquent.PermissionError(_("You do not have permission to view this document"))


def validate_key(key: str, doc: "Document") -> None:
	document_key_expiry = traquent.get_cached_value(
		"Document Share Key",
		{"reference_doctype": doc.doctype, "reference_docname": doc.name, "key": key},
		["expires_on"],
	)
	if document_key_expiry is not None:
		if is_expired(document_key_expiry[0]):
			raise traquent.exceptions.LinkExpired
		else:
			return

	# TODO: Deprecate this! kept it for backward compatibility
	if traquent.get_system_settings("allow_older_web_view_links") and key == doc.get_signature():
		return

	raise traquent.exceptions.InvalidKeyError


def get_letter_head(doc: "Document", no_letterhead: bool, letterhead: str | None = None) -> dict:
	if no_letterhead:
		return {}

	letterhead_name = letterhead or doc.get("letter_head")
	if letterhead_name:
		return traquent.db.get_value(
			"Letter Head",
			letterhead_name,
			["content", "footer", "header_script", "footer_script"],
			as_dict=True,
		)
	else:
		return (
			traquent.db.get_value(
				"Letter Head",
				{"is_default": 1},
				["content", "footer", "header_script", "footer_script"],
				as_dict=True,
			)
			or {}
		)


def get_print_format(doctype: str, print_format: "PrintFormat") -> str:
	if print_format.disabled:
		traquent.throw(_("Print Format {0} is disabled").format(print_format.name), traquent.DoesNotExistError)

	# server, find template
	module = print_format.module or traquent.db.get_value("DocType", doctype, "module")
	path = os.path.join(
		get_module_path(module, "Print Format", print_format.name),
		traquent.scrub(print_format.name) + ".html",
	)

	if os.path.exists(path):
		with open(path) as pffile:
			return pffile.read()
	else:
		if print_format.raw_printing:
			return print_format.raw_commands
		if print_format.html:
			return print_format.html

		traquent.throw(_("No template found at path: {0}").format(path), traquent.TemplateNotFoundError)


def make_layout(doc: "Document", meta: "Meta", format_data=None) -> list:
	"""Builds a hierarchical layout object from the fields list to be rendered
	by `standard.html`

	:param doc: Document to be rendered.
	:param meta: Document meta object (doctype).
	:param format_data: Fields sequence and properties defined by Print Format Builder."""
	layout, page = [], []
	layout.append(page)

	def get_new_section():
		return {"columns": [], "has_data": False}

	def append_empty_field_dict_to_page_column(page):
		"""append empty columns dict to page layout"""
		if not page[-1]["columns"]:
			page[-1]["columns"].append({"fields": []})

	for df in format_data or meta.fields:
		if format_data:
			# embellish df with original properties
			df = traquent._dict(df)
			if df.fieldname:
				original = meta.get_field(df.fieldname)
				if original:
					newdf = original.as_dict()
					newdf.hide_in_print_layout = original.get("hide_in_print_layout")
					newdf.update(df)
					df = newdf

			df.print_hide = 0

		if df.fieldtype == "Section Break" or page == []:
			if len(page) > 1:
				if not page[-1]["has_data"]:
					# truncate last section if empty
					del page[-1]

			section = get_new_section()
			if df.fieldtype == "Section Break" and df.label:
				section["label"] = df.label

			page.append(section)

		elif df.fieldtype == "Column Break":
			# if last column break and last column is not empty
			page[-1]["columns"].append({"fields": []})

		else:
			# add a column if not yet added
			append_empty_field_dict_to_page_column(page)

		if df.fieldtype == "HTML" and df.options:
			doc.set(df.fieldname, True)  # show this field

		if df.fieldtype == "Signature" and not doc.get(df.fieldname):
			placeholder_image = "/assets/traquent/images/signature-placeholder.png"
			doc.set(df.fieldname, placeholder_image)

		if is_visible(df, doc) and has_value(df, doc):
			append_empty_field_dict_to_page_column(page)

			page[-1]["columns"][-1]["fields"].append(df)

			# section has fields
			page[-1]["has_data"] = True

			# if table, add the row info in the field
			# if a page break is found, create a new docfield
			if df.fieldtype == "Table":
				df.rows = []
				df.start = 0
				df.end = None
				for i, row in enumerate(doc.get(df.fieldname)):
					if row.get("page_break"):
						# close the earlier row
						df.end = i

						# new page, with empty section and column
						page = [get_new_section()]
						layout.append(page)
						append_empty_field_dict_to_page_column(page)

						# continue the table in a new page
						df = copy.copy(df)
						df.start = i
						df.end = None
						page[-1]["columns"][-1]["fields"].append(df)

	return layout


def is_visible(df: "DocField", doc: "Document") -> bool:
	"""Return True if docfield is visible in print layout and does not have print_hide set."""
	if df.fieldtype in ("Section Break", "Column Break", "Button"):
		return False

	if (df.permlevel or 0) > 0 and not doc.has_permlevel_access_to(df.fieldname, df):
		return False

	return not doc.is_print_hide(df.fieldname, df)


def has_value(df: "DocField", doc: "Document") -> bool:
	"""Return True if given docfield (`df`) has some value in the given document (`doc`)."""
	value = doc.get(df.fieldname)
	if value in (None, ""):
		return False

	elif isinstance(value, str) and not strip_html(value).strip():
		if df.fieldtype in ["Text", "Text Editor"]:
			return True

		return False

	elif isinstance(value, list) and not len(value):
		return False

	return True


def get_print_style(
	style: str | None = None, print_format: Optional["PrintFormat"] = None, for_legacy: bool = False
) -> str:
	print_settings = traquent.get_doc("Print Settings")

	if not style:
		style = print_settings.print_style or ""

	context = {
		"print_settings": print_settings,
		"print_style": style,
		"font": get_font(print_settings, print_format, for_legacy),
	}

	css = traquent.get_template("templates/styles/standard.css").render(context)

	if style and traquent.db.exists("Print Style", style):
		css = css + "\n" + traquent.db.get_value("Print Style", style, "css")

	# move @import to top
	for at_import in list(set(re.findall(r"(@import url\([^\)]+\)[;]?)", css))):
		css = css.replace(at_import, "")

		# prepend css with at_import
		css = at_import + css

	if print_format and print_format.css:
		css += "\n\n" + print_format.css

	return css


def get_font(
	print_settings: "PrintSettings", print_format: Optional["PrintFormat"] = None, for_legacy=False
) -> str:
	default = "var(--font-stack)"
	if for_legacy:
		return default

	font = None
	if print_format:
		if print_format.font and print_format.font != "Default":
			font = f"{print_format.font}, sans-serif"

	if not font:
		if print_settings.font and print_settings.font != "Default":
			font = f"{print_settings.font}, sans-serif"

		else:
			font = default

	return font


def get_visible_columns(data: list, table_meta: "Meta", df: "DocField") -> list["DocField"]:
	"""Return list of visible columns based on print_hide and if all columns have value."""
	columns = []
	doc = data[0] or traquent.new_doc(df.options)

	hide_in_print_layout = df.get("hide_in_print_layout") or []

	def add_column(col_df: "DocField"):
		if col_df.fieldname in hide_in_print_layout:
			return False
		return is_visible(col_df, doc) and column_has_value(data, col_df.get("fieldname"), col_df)

	if df.get("visible_columns"):
		# columns specified by column builder
		for col_df in df.get("visible_columns"):
			# load default docfield properties
			docfield = table_meta.get_field(col_df.get("fieldname"))
			if not docfield:
				continue
			newdf = docfield.as_dict().copy()
			newdf.update(col_df)
			if add_column(newdf):
				columns.append(newdf)
	else:
		for col_df in table_meta.fields:
			if add_column(col_df):
				columns.append(col_df)

	return columns


def column_has_value(data: list, fieldname: str, col_df: "DocField") -> bool:
	"""Check if at least one cell in column has non-zero and non-blank value"""
	has_value = False

	if col_df.fieldtype in ["Float", "Currency"] and not col_df.print_hide_if_no_value:
		return True

	for row in data:
		value = row.get(fieldname)
		if value:
			if isinstance(value, str):
				if strip_html(value).strip():
					has_value = True
					break
			else:
				has_value = True
				break

	return has_value


trigger_print_script = """
<script>
//allow wrapping of long tr
var elements = document.getElementsByTagName("tr");
var i = elements.length;
while (i--) {
	if(elements[i].clientHeight>300){
		elements[i].setAttribute("style", "page-break-inside: auto;");
	}
}

window.print();

// close the window after print
// NOTE: doesn't close if print is cancelled in Chrome
// Changed timeout to 5s from 1s because it blocked mobile view rendering
setTimeout(function() {
	window.close();
}, 5000);
</script>
"""
