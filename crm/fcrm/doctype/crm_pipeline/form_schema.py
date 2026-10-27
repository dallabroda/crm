# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Form schema: the fields a form shows in a context, in order (dynamic forms, credtech#178).

Cards: the pipeline decides which fields and their order (CRM Pipeline Field); the stage decides visible,
required and read only (CRM Pipeline Field Rule). Without a stage the answer covers "all stages": a flag is
returned when the stages agree, None when they differ (`varies`). Contacts and companies have one global
form; until its own configuration exists (phase 3) it follows the side panel layout.
"""

import frappe
from frappe import _

from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import (
	get_field_obj,
	get_sidepanel_sections,
	handle_perm_level_restrictions,
)
from crm.fcrm.doctype.crm_pipeline import fields as catalog

# Always shown, cannot be hidden (owner decisions of 27/10/2026)
LOCKED_FIELDS = {
	catalog.DEAL: catalog.LOCKED_FIELDS,
	"Contact": ("first_name",),
	"CRM Organization": ("organization_name",),
}
RULE_FLAGS = ("visible", "required", "read_only")


def get_form_schema(doctype: str, pipeline: str | None = None, stage: str | None = None) -> dict:
	doctype = catalog._form_doctype(doctype)
	if doctype == catalog.DEAL:
		if not pipeline:
			frappe.throw(_("Choose a pipeline."))
		rows = _card_rows(pipeline, stage)
	else:
		rows = _global_rows(doctype)
	meta = frappe.get_meta(doctype)
	fields = [_field(doctype, meta, row) for row in rows]
	return {"doctype": doctype, "pipeline": pipeline, "stage": stage, "fields": [f for f in fields if f]}


def _locked_rows(doctype: str, meta) -> list[dict]:
	rows = []
	for fieldname in LOCKED_FIELDS.get(doctype, ()):
		df = meta.get_field(fieldname)
		if df:
			rows.append(
				{
					"fieldname": fieldname,
					"visible": 1,
					"required": int(bool(df.reqd)),
					"read_only": 0,
					"locked": 1,
				}
			)
	return rows


def _card_rows(pipeline: str, stage: str | None) -> list[dict]:
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	meta = frappe.get_meta(catalog.DEAL)
	if stage:
		stages = [stage]
	else:
		stages = frappe.get_all(
			"CRM Deal Status", {"pipeline": pipeline}, pluck="name", order_by="position asc, creation asc"
		)
	rules = {(r.stage, r.fieldname): r for r in doc.field_rules}
	rows = _locked_rows(catalog.DEAL, meta)
	for field in sorted(doc.fields, key=lambda f: (f.position or 0, f.idx)):
		df = meta.get_field(field.fieldname)
		# a created field that was disabled keeps its values but is no longer shown
		if not df or (field.fieldname.startswith(catalog.CREATED_PREFIX) and df.hidden):
			continue
		row = {"fieldname": field.fieldname, "locked": 0, "varies": {}}
		for flag in RULE_FLAGS:
			default = 1 if flag == "visible" else 0
			values = {int(getattr(rules.get((s, field.fieldname)), flag, default)) for s in stages} or {
				default
			}
			# all stages agree: their value; otherwise None and `varies`
			row[flag] = next(iter(values)) if len(values) == 1 else None
			row["varies"][flag] = len(values) > 1
		rows.append(row)
	return rows


def _global_rows(doctype: str) -> list[dict]:
	"""Contacts and companies: the side panel layout order, then created fields it does not have yet."""
	meta = frappe.get_meta(doctype)
	rows = _locked_rows(doctype, meta)
	seen = {r["fieldname"] for r in rows}
	order = []
	for section in get_sidepanel_sections(doctype):
		for column in section.get("columns") or []:
			for field in column.get("fields") or []:
				order.append(field.get("fieldname") if isinstance(field, dict) else field)
	created = [
		df.fieldname
		for df in meta.fields
		if df.fieldname.startswith(catalog.CREATED_PREFIX) and not df.hidden
	]
	for fieldname in [*order, *created]:
		df = meta.get_field(fieldname) if fieldname else None
		if not df or fieldname in seen:
			continue
		seen.add(fieldname)
		rows.append(
			{
				"fieldname": fieldname,
				"visible": 1,
				"required": int(bool(df.reqd)),
				"read_only": int(bool(df.read_only)),
				"locked": 0,
			}
		)
	return rows


def _field(doctype: str, meta, row: dict) -> dict | None:
	df = meta.get_field(row["fieldname"])
	if not df:
		return None
	field = df.as_dict()
	handle_perm_level_restrictions(field, doctype)
	# what the form uses to render: required and read-only come from the context
	field["reqd"] = int(bool(row["required"]))
	field["read_only"] = int(bool(row["read_only"] or field.get("read_only")))
	field = get_field_obj(field)
	field.update(
		{
			"visible": row["visible"],
			"required": row["required"],
			"locked": row["locked"],
			"read_only_rule": row["read_only"],
			"is_created": int(row["fieldname"].startswith(catalog.CREATED_PREFIX)),
			"varies": row.get("varies") or {},
		}
	)
	return field
