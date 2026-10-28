# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Dynamic forms API (credtech#178): the form of cards, contacts and companies in a context.

Routes /api/method/crm.api.forms.* (prefix agreed with the API keys proposal). Cards: the funnel decides
which fields and their order, the stage decides visible, required and read only, and "all stages" is a
batch edit of every stage (proposal, section 3.2). Contacts and companies have one form each (phase 3).
"""

import json

import frappe
from frappe import _

from crm.api.pipeline import (
	CRM_ROLES,
	_assert_admin,
	_assert_can_manage,
	_assert_can_view,
	_stages,
	save_pipeline,
)
from crm.fcrm.doctype.crm_pipeline import fields as catalog
from crm.fcrm.doctype.crm_pipeline import form_schema

RULE_FLAGS = form_schema.RULE_FLAGS


def _json(value):
	return json.loads(value) if isinstance(value, str) else value


@frappe.whitelist()
def get_form_schema(doctype: str, pipeline: str | None = None, stage: str | None = None) -> dict:
	"""Fields of the form in order, each with visible, required, read only and locked for the context."""
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if doctype == catalog.DEAL and pipeline:
		_assert_can_view(pipeline)
	return form_schema.get_form_schema(doctype, pipeline, stage)


@frappe.whitelist()
def save_form_config(
	doctype: str, fields: str | list, pipeline: str | None = None, stage: str | None = None
) -> dict:
	"""Save the form of a context and answer with its new schema.

	fields: [{fieldname, visible, required, read_only}] in the form's order. Locked fields are always
	shown and are ignored here. Cards: the list and the order become the funnel's; the flags go to
	`stage`, or to every stage when there is none. A flag left out or None keeps each stage's own value
	(what the screen shows as "varies by stage").
	"""
	doctype = catalog._form_doctype(doctype)
	if doctype != catalog.DEAL:
		# contacts and companies: one form for the whole company, set by admins
		_assert_admin()
		return form_schema.save_global_form(doctype, _json(fields) or [])
	if not pipeline:
		frappe.throw(_("Choose a pipeline."))
	_assert_can_manage(pipeline)

	locked = set(form_schema.LOCKED_FIELDS[catalog.DEAL])
	rows = [frappe._dict(r) for r in _json(fields) or [] if r.get("fieldname") not in locked]
	fieldnames = [r.fieldname for r in rows]
	repeated = {f for f in fieldnames if fieldnames.count(f) > 1}
	if repeated:
		frappe.throw(_("Field {0} appears more than once.").format(frappe.bold(", ".join(sorted(repeated)))))

	stages = [s.name for s in _stages(pipeline)]
	if stage and stage not in stages:
		frappe.throw(_("Stage {0} is not in this pipeline.").format(frappe.bold(stage)))

	field_rules = []
	for row in rows:
		flags = {flag: frappe.utils.cint(row[flag]) for flag in RULE_FLAGS if row.get(flag) is not None}
		# required implies visible; a hidden field is neither required nor read only
		if flags.get("required") or flags.get("read_only"):
			flags["visible"] = 1
		if flags.get("visible") == 0:
			flags.update(required=0, read_only=0)
		for name in [stage] if stage else stages:
			field_rules.append({"stage": name, "fieldname": row.fieldname, **flags})

	save_pipeline({"name": pipeline, "fields": fieldnames, "field_rules": field_rules})
	return form_schema.get_form_schema(doctype, pipeline, stage)


@frappe.whitelist()
def get_fields(doctype: str) -> dict:
	"""Fields of a form's catalog, with the created-field limit and the room left in the table."""
	frappe.only_for(CRM_ROLES)
	doctype = catalog._form_doctype(doctype)
	fields = catalog.get_catalog() if doctype == catalog.DEAL else form_schema.form_catalog(doctype)
	return {
		"limit": catalog.CREATED_FIELD_LIMIT,
		"used": catalog.created_field_count(doctype),
		"room": catalog.room_by_type(doctype),
		"fields": fields,
	}


@frappe.whitelist()
def create_field(
	label: str,
	fieldtype: str,
	options: str | None = None,
	doctype: str = catalog.DEAL,
	placement: str | list | None = None,
	required: bool = False,
) -> dict:
	"""Create a field. Cards: `placement` [{pipeline, stages}] puts it at the end of those funnels,
	visible only in `stages` (every stage when empty) and required there when `required`."""
	_assert_admin()
	doctype = catalog._form_doctype(doctype)
	placement = [frappe._dict(p) for p in _json(placement) or []]
	if placement and doctype != catalog.DEAL:
		frappe.throw(_("Only card fields go into funnels."))
	# checked before the field exists: creating it changes the table and cannot be rolled back
	for place in placement:
		stages = {s.name for s in _stages(place.pipeline)}
		unknown = set(place.stages or []) - stages
		if not frappe.db.exists("CRM Pipeline", place.pipeline) or unknown:
			frappe.throw(_("Choose stages of the pipeline {0}.").format(frappe.bold(place.pipeline)))

	field = catalog.create_field(label, fieldtype, options, doctype)
	for place in placement:
		_put_in_pipeline(field["fieldname"], place.pipeline, place.stages, frappe.utils.sbool(required))
	return field


def _put_in_pipeline(fieldname: str, pipeline: str, stages: list[str] | None, required: bool):
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	used = [f.fieldname for f in sorted(doc.fields, key=lambda f: (f.position or 0, f.idx))]
	all_stages = [s.name for s in _stages(pipeline)]
	shown = set(stages or all_stages)
	save_pipeline(
		{
			"name": pipeline,
			"fields": [*used, fieldname],
			"field_rules": [
				{
					"stage": stage,
					"fieldname": fieldname,
					"visible": int(stage in shown),
					"required": int(required and stage in shown),
					"read_only": 0,
				}
				for stage in all_stages
			],
		}
	)


@frappe.whitelist()
def update_field(
	fieldname: str, label: str | None = None, options: str | None = None, doctype: str = catalog.DEAL
) -> dict:
	_assert_admin()
	return catalog.update_field(fieldname, label, options, doctype)


@frappe.whitelist()
def disable_field(fieldname: str, doctype: str = catalog.DEAL) -> dict:
	_assert_admin()
	return catalog.disable_field(fieldname, doctype)
