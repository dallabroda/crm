# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Form schema: the fields a form shows in a context, in order (dynamic forms, credtech#178).

Cards: the pipeline decides which fields and their order (CRM Pipeline Field); the stage decides visible,
required and read only (CRM Pipeline Field Rule). Without a stage the answer covers "all stages": a flag is
returned when the stages agree, None when they differ (`varies`). Contacts and companies have one global
form, saved in CRM Form Config (phase 3, credtech#181).
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


def get_form_schema(
	doctype: str, pipeline: str | None = None, stage: str | None = None, block: str | None = None
) -> dict:
	"""Cards also take a block (credtech#196): the card's own fields (default) or the fields of its organization,
	second organization or primary contact that the funnel shows on the card, stage by stage."""
	doctype = catalog._form_doctype(doctype)
	block = block or catalog.CARD
	if doctype == catalog.DEAL:
		if not pipeline:
			frappe.throw(_("Choose a pipeline."))
		if block not in catalog.BLOCKS:
			frappe.throw(_("Unknown block {0}.").format(frappe.bold(block)))
		rows = _card_rows(pipeline, stage, block)
	else:
		rows = _global_rows(doctype)
	fields_doctype = catalog.BLOCK_DOCTYPES[block] if doctype == catalog.DEAL else doctype
	meta = frappe.get_meta(fields_doctype)
	fields = [_field(fields_doctype, meta, row) for row in rows]
	schema = {"doctype": doctype, "pipeline": pipeline, "stage": stage, "fields": [f for f in fields if f]}
	if doctype == catalog.DEAL:
		# the funnel may name the card's second organization (e.g. "Debtor", credtech#195)
		from crm.api.card_contacts import second_organization_label

		label = second_organization_label(pipeline)
		schema["second_organization_label"] = label
		schema["block"] = block
		schema["block_doctype"] = fields_doctype
		schema["blocks"] = [
			{
				"block": b,
				"doctype": catalog.BLOCK_DOCTYPES[b],
				"label": label if b == catalog.SECOND_ORGANIZATION else _(b),
			}
			for b in catalog.BLOCKS
		]
		for field in schema["fields"]:
			if block == catalog.CARD and field["fieldname"] == "second_organization":
				field["label"] = label
	if doctype != catalog.DEAL:
		# until the company saves this form, its screens keep the side panel layout
		schema["configured"] = frappe.db.exists(FORM_CONFIG, doctype) is not None
	return schema


def _locked_rows(doctype: str, meta) -> list[dict]:
	rows = []
	for fieldname in LOCKED_FIELDS.get(doctype, ()):
		df = meta.get_field(fieldname)
		if df:
			rows.append(
				{
					"fieldname": fieldname,
					"visible": 1,
					# the card's name is required on screen; the server fills it when an entry leaves it empty
					"required": int(bool(df.reqd) or fieldname == "deal_name"),
					"read_only": 0,
					"locked": 1,
				}
			)
	return rows


def _card_rows(pipeline: str, stage: str | None, block: str = catalog.CARD) -> list[dict]:
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	meta = frappe.get_meta(catalog.BLOCK_DOCTYPES[block])
	if stage:
		stages = [stage]
	else:
		stages = frappe.get_all(
			"CRM Deal Status", {"pipeline": pipeline}, pluck="name", order_by="position asc, creation asc"
		)
	rules = {(r.stage, r.fieldname): r for r in doc.field_rules if catalog.block_of(r) == block}
	rows = _locked_rows(catalog.DEAL, meta) if block == catalog.CARD else []
	used = [f for f in doc.fields if catalog.block_of(f) == block]
	for field in sorted(used, key=lambda f: (f.position or 0, f.idx)):
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


# Fields of contacts and companies that are not part of their form: bookkeeping of lookups, sync and system data,
# and repeated or unused fields the owner took out on 28/10/2026 (the values stay saved): territory; the Receita
# legal and trade names (the organization name becomes the legal name when the CNPJ is filled); the employee
# count and range found by the company lookup (the employees field keeps the standard range); a contact's
# salutation, gender, address, middle and last name (one full name). A contact's company_name stays: it is the
# contact's organization (the screens show it as Organization)
NOT_IN_FORM = {
	"CRM Organization": (
		"territory",
		"legal_name",
		"trade_name",
		"employee_count",
		"employee_range",
		"currency",
		"exchange_rate",
		"organization_logo",
		"cnpj_checked_on",
		"company_checked_on",
		"employee_source",
	),
	"Contact": (
		"salutation",
		"gender",
		"address",
		"middle_name",
		"last_name",
		"full_name",
		"user",
		"image",
		"status",
		"is_primary_contact",
		"unsubscribed",
		"sync_with_google_contacts",
		"google_contacts",
		"google_contacts_id",
		"pulled_from_google_contacts",
	),
}
FORM_CONFIG = "CRM Form Config"
# Read-only in the doctype but filled by the record from its tables (a contact's primary e-mail and mobile, which
# the screens turn into table rows), so the person does fill them in: they can be required. `phone` is not: the
# screens do not turn it into a row, so Contact.validate clears it (review of crm#53)
FILLED_FROM_TABLES = {"Contact": ("email_id", "mobile_no")}


def can_require(doctype: str, df) -> bool:
	"""Read-only fields are filled by the system: they can be shown, not required."""
	return not df.read_only or df.fieldname in FILLED_FROM_TABLES.get(doctype, ())


def form_catalog(doctype: str) -> list[dict]:
	"""Contacts and companies: their own fields (native, including the Receita Federal data the CNPJ lookup
	fills, and created ones), each saying whether it is locked and whether it can be required (read-only
	fields are filled by the system, so they can be shown but not required)."""
	meta = frappe.get_meta(doctype)
	locked = LOCKED_FIELDS.get(doctype, ())
	skip = set(NOT_IN_FORM.get(doctype, ()))
	fields = []
	for df in meta.fields:
		if (
			df.fieldtype in frappe.model.no_value_fields
			or df.fieldtype in frappe.model.table_fields
			or df.fieldname in skip
		):
			continue
		created = df.fieldname.startswith(catalog.CREATED_PREFIX)
		if df.hidden and not created:
			continue
		info = catalog._field_info(df, not created)
		info["locked"] = int(df.fieldname in locked)
		info["can_require"] = int(can_require(doctype, df))
		fields.append(info)
	return fields


def _layout_order(doctype: str) -> list[str]:
	order = []
	for section in get_sidepanel_sections(doctype):
		for column in section.get("columns") or []:
			for field in column.get("fields") or []:
				order.append(field.get("fieldname") if isinstance(field, dict) else field)
	return order


def _saved_config(doctype: str) -> list[dict] | None:
	if not frappe.db.exists(FORM_CONFIG, doctype):
		return None
	rows = frappe.get_doc(FORM_CONFIG, doctype).fields
	return [r.as_dict() for r in sorted(rows, key=lambda r: (r.position or 0, r.idx))]


def _global_rows(doctype: str) -> list[dict]:
	"""Contacts and companies: the saved form (CRM Form Config). Before it is first saved, the side panel layout
	order is the form (those fields visible), then the created fields (visible), then the other native fields
	(hidden). Fields created after the form was saved come at the end, visible."""
	meta = frappe.get_meta(doctype)
	rows = _locked_rows(doctype, meta)
	seen = {r["fieldname"] for r in rows}
	fields = {f["fieldname"]: f for f in form_catalog(doctype) if not f["disabled"]}
	saved = _saved_config(doctype)
	if saved is not None:
		ordered = [(r.fieldname, r.visible, r.required) for r in saved]
		rest = [(f, 1, 0) for f in fields if f.startswith(catalog.CREATED_PREFIX)]
		rest += [(f, 0, 0) for f in fields if not f.startswith(catalog.CREATED_PREFIX)]
	else:
		layout = _layout_order(doctype)
		ordered = [(f, 1, 0) for f in layout]
		rest = [(f, 1, 0) for f in fields if f.startswith(catalog.CREATED_PREFIX)]
		rest += [(f, 0, 0) for f in fields if not f.startswith(catalog.CREATED_PREFIX)]
	for fieldname, visible, required in [*ordered, *rest]:
		field = fields.get(fieldname)
		if not field or fieldname in seen:
			continue
		seen.add(fieldname)
		df = meta.get_field(fieldname)
		rows.append(
			{
				"fieldname": fieldname,
				"visible": int(bool(visible or required)),
				"required": int(bool(required) and field["can_require"]),
				# shown as "read only": filled by the system, not by the person
				"read_only": int(not can_require(doctype, df)),
				"locked": 0,
			}
		)
	return rows


def save_global_form(doctype: str, rows: list[dict]) -> dict:
	"""Save the form of contacts or companies: the order and, for each field, visible and required.
	Locked fields are always shown and are ignored here; required implies visible."""
	fields = {f["fieldname"]: f for f in form_catalog(doctype) if not f["disabled"]}
	locked = set(LOCKED_FIELDS.get(doctype, ()))
	saved, seen = [], set()
	for row in rows:
		row = frappe._dict(row)
		if row.fieldname in locked:
			continue
		field = fields.get(row.fieldname)
		if not field:
			frappe.throw(_("Field {0} is not in this form.").format(frappe.bold(row.fieldname)))
		if row.fieldname in seen:
			frappe.throw(_("Field {0} appears more than once.").format(frappe.bold(row.fieldname)))
		seen.add(row.fieldname)
		required = frappe.utils.cint(row.get("required"))
		if required and not field["can_require"]:
			frappe.throw(
				_("{0} is filled in by the system and cannot be required.").format(
					frappe.bold(_(field["label"]))
				)
			)
		visible = 1 if required else frappe.utils.cint(row.get("visible", 1))
		saved.append(
			{"fieldname": row.fieldname, "position": len(saved) + 1, "visible": visible, "required": required}
		)
	if frappe.db.exists(FORM_CONFIG, doctype):
		config = frappe.get_doc(FORM_CONFIG, doctype)
	else:
		config = frappe.new_doc(FORM_CONFIG)
		config.form_doctype = doctype
	config.set("fields", saved)
	config.save(ignore_permissions=True)
	return get_form_schema(doctype)


def _direct_entry(doc) -> bool:
	"""The record is being created by itself (its own form or the REST API), not as a side effect of another
	flow (converting a lead, a card with a new company, a CNPJ lookup) nor by an automatic entry."""
	if frappe.flags.get("crm_automatic_entry"):
		return False
	form = frappe.local.form_dict
	if (form.get("cmd") or "") in ("frappe.client.insert", "frappe.client.save"):
		# only when the request's own document is this record's doctype
		sent = form.get("doc")
		sent = frappe.parse_json(sent) if isinstance(sent, str) else sent
		return isinstance(sent, dict) and sent.get("doctype") == doc.doctype
	request = getattr(frappe.local, "request", None)
	path = getattr(request, "path", "") or ""
	return path.startswith((f"/api/resource/{doc.doctype}", f"/api/v2/document/{doc.doctype}"))


def validate_required(doc, method=None):
	"""validate of contacts and companies: the form's required fields (dynamic forms, credtech#181).
	Creating the record directly needs them; once saved, a required field that was filled cannot be emptied.
	Records saved before the field became required are not blocked until someone fills the field."""
	saved = _saved_config(doc.doctype)
	if not saved or frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return
	before = None if doc.is_new() else doc.get_doc_before_save()
	creating = doc.is_new() and _direct_entry(doc)
	missing = []
	for row in saved:
		df = doc.meta.get_field(row.fieldname)
		if (
			not row.required
			or not df
			or not can_require(doc.doctype, df)
			or not catalog.is_empty(df, doc.get(row.fieldname))
		):
			continue
		emptied = before is not None and not catalog.is_empty(df, before.get(row.fieldname))
		if creating or emptied:
			missing.append(_(df.label))
	if missing:
		frappe.throw(_("Fill in: {0}").format(", ".join(missing)), title=_("Required fields"))


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
			"can_require": int(can_require(doctype, df)),
			"varies": row.get("varies") or {},
		}
	)
	return field
