# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Company field catalog for cards and the per-stage rules (visible / required / read only)."""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

DEAL = "CRM Deal"
# Created fields get this prefix, so they are told apart from standard and app fields
CREATED_PREFIX = "ch_"
CREATED_FIELD_LIMIT = 80
# Always shown and editable: a card cannot exist without them
LOCKED_FIELDS = ("pipeline", "status", "deal_owner")
STANDARD_FIELDS = (
	"organization",
	"deal_value",
	"expected_deal_value",
	"expected_closure_date",
	"probability",
	"next_step",
	"source",
	"website",
	"annual_revenue",
	"no_of_employees",
	"industry",
	"territory",
	"currency",
	"lost_reason",
	"lost_notes",
)
FIELD_TYPES = ("Data", "Int", "Float", "Currency", "Date", "Select", "Check", "Attach", "Link")
LINK_TARGETS = ("Contact", "CRM Organization")
NUMBER_TYPES = ("Int", "Float", "Currency", "Percent")


class MissingRequiredFieldsError(frappe.ValidationError):
	pass


def _field_info(df, is_standard: bool) -> dict:
	return {
		"fieldname": df.fieldname,
		"label": df.label,
		"fieldtype": df.fieldtype,
		"options": df.options or "",
		"is_standard": int(is_standard),
		"locked": int(df.fieldname in LOCKED_FIELDS),
		"disabled": int(bool(df.hidden)) if not is_standard else 0,
	}


def get_catalog(include_disabled: bool = True) -> list[dict]:
	"""Locked + standard fields, fields added by installed apps, then fields created by the company."""
	meta = frappe.get_meta(DEAL)
	catalog, seen = [], set()
	for fieldname in (*LOCKED_FIELDS, *STANDARD_FIELDS):
		df = meta.get_field(fieldname)
		if df:
			catalog.append(_field_info(df, True))
			seen.add(fieldname)
	for df in meta.fields:
		if (
			df.fieldname in seen
			or not df.get("is_custom_field")
			or df.fieldtype in frappe.model.no_value_fields
		):
			continue
		created = df.fieldname.startswith(CREATED_PREFIX)
		if not created and df.hidden:
			continue
		info = _field_info(df, not created)
		if info["disabled"] and not include_disabled:
			continue
		catalog.append(info)
	return catalog


def catalog_fieldnames() -> set[str]:
	return {f["fieldname"] for f in get_catalog(include_disabled=False)}


def created_field_count() -> int:
	return frappe.db.count("Custom Field", {"dt": DEAL, "fieldname": ("like", f"{CREATED_PREFIX}%")})


def create_field(label: str, fieldtype: str, options: str | None = None) -> dict:
	label = (label or "").strip()
	if not label:
		frappe.throw(_("Give the field a name."))
	if fieldtype not in FIELD_TYPES:
		frappe.throw(_("Field type {0} is not supported.").format(frappe.bold(fieldtype)))
	if created_field_count() >= CREATED_FIELD_LIMIT:
		frappe.throw(_("The limit of {0} created fields was reached.").format(CREATED_FIELD_LIMIT))
	options = _clean_options(fieldtype, options)

	base = CREATED_PREFIX + (frappe.scrub(label)[:50] or "field")
	fieldname, n = base, 1
	meta = frappe.get_meta(DEAL)
	while meta.has_field(fieldname) or frappe.db.exists("Custom Field", {"dt": DEAL, "fieldname": fieldname}):
		n += 1
		fieldname = f"{base}_{n}"

	create_custom_field(
		DEAL,
		{
			"fieldname": fieldname,
			"label": label,
			"fieldtype": fieldtype,
			"options": options,
			"insert_after": _last_fieldname(),
		},
		ignore_validate=False,
	)
	frappe.clear_cache(doctype=DEAL)
	return _catalog_item(fieldname)


def update_field(fieldname: str, label: str | None = None, options: str | None = None) -> dict:
	cf = _created_custom_field(fieldname)
	if label is not None:
		label = label.strip()
		if not label:
			frappe.throw(_("Give the field a name."))
		cf.label = label
	if options is not None:
		cf.options = _clean_options(cf.fieldtype, options)
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype=DEAL)
	return _catalog_item(fieldname)


def disable_field(fieldname: str) -> dict:
	"""Hide a created field everywhere; its column and values are kept."""
	cf = _created_custom_field(fieldname)
	cf.hidden = 1
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype=DEAL)
	return _catalog_item(fieldname)


def _created_custom_field(fieldname: str):
	if not (fieldname or "").startswith(CREATED_PREFIX):
		frappe.throw(_("Only fields created by the company can be changed."))
	name = frappe.db.get_value("Custom Field", {"dt": DEAL, "fieldname": fieldname})
	if not name:
		frappe.throw(_("Field {0} not found.").format(frappe.bold(fieldname)), frappe.DoesNotExistError)
	return frappe.get_doc("Custom Field", name)


def _clean_options(fieldtype: str, options: str | None) -> str | None:
	if fieldtype == "Select":
		values = [v.strip() for v in (options or "").splitlines() if v.strip()]
		if not values:
			frappe.throw(_("List the options, one per line."))
		return "\n".join(values)
	if fieldtype == "Link":
		if options not in LINK_TARGETS:
			frappe.throw(_("A link field points to a contact or an organization."))
		return options
	if fieldtype == "Currency":
		return "currency"
	return None


def _last_fieldname() -> str:
	fields = [df.fieldname for df in frappe.get_meta(DEAL).fields]
	return fields[-1] if fields else "status"


def _catalog_item(fieldname: str) -> dict:
	return next(f for f in get_catalog() if f["fieldname"] == fieldname)


# Rules ---------------------------------------------------------------------


def default_pipeline_fields() -> list[str]:
	"""Fields a new pipeline starts with: the standard ones."""
	meta = frappe.get_meta(DEAL)
	return [f for f in STANDARD_FIELDS if meta.has_field(f)]


def setup_default_fields(pipeline: str):
	"""Give a pipeline that has no fields yet the standard ones, with default rules."""
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	if doc.fields:
		return
	doc.set(
		"fields", [{"fieldname": f, "position": i} for i, f in enumerate(default_pipeline_fields(), start=1)]
	)
	stages = frappe.get_all(
		"CRM Deal Status", {"pipeline": pipeline}, pluck="name", order_by="position asc, creation asc"
	)
	sync_rules(doc, stages)
	doc.save(ignore_permissions=True)


def sync_rules(pipeline_doc, stages: list[str]):
	"""Keep exactly one rule per (used field, stage); new pairs start visible, optional, editable."""
	used = [f.fieldname for f in pipeline_doc.fields]
	existing = {(r.stage, r.fieldname): r for r in pipeline_doc.field_rules}
	rows = []
	for stage in stages:
		for fieldname in used:
			rule = existing.get((stage, fieldname))
			rows.append(
				{
					"stage": stage,
					"fieldname": fieldname,
					"visible": rule.visible if rule else 1,
					"required": rule.required if rule else 0,
					"read_only": rule.read_only if rule else 0,
				}
			)
	pipeline_doc.set("field_rules", rows)


def validate_pipeline_fields(pipeline_doc):
	"""New fields must come from the catalog. Fields already in the pipeline stay even if disabled
	(values are kept); fields that no longer exist at all are dropped with their rules."""
	before = pipeline_doc.get_doc_before_save()
	already_used = {row.fieldname for row in before.fields} if before else set()
	meta = frappe.get_meta(DEAL)
	gone = {f for f in already_used if not meta.has_field(f)}
	if gone:
		pipeline_doc.set("fields", [row for row in pipeline_doc.fields if row.fieldname not in gone])
		pipeline_doc.set("field_rules", [r for r in pipeline_doc.field_rules if r.fieldname not in gone])

	available = catalog_fieldnames() | (already_used - gone)
	seen = set()
	for row in pipeline_doc.fields:
		if row.fieldname in LOCKED_FIELDS:
			frappe.throw(
				_("{0} is always shown and does not need to be added.").format(frappe.bold(row.fieldname))
			)
		if row.fieldname not in available:
			frappe.throw(_("Field {0} is not in the field catalog.").format(frappe.bold(row.fieldname)))
		if row.fieldname in seen:
			frappe.throw(_("Field {0} was added twice.").format(frappe.bold(row.fieldname)))
		seen.add(row.fieldname)
	for rule in pipeline_doc.field_rules:
		if rule.required and not rule.visible:
			frappe.throw(_("A required field must be visible ({0}).").format(frappe.bold(rule.fieldname)))


def get_stage_rules(pipeline: str, stage: str) -> dict:
	rules = frappe.get_all(
		"CRM Pipeline Field Rule",
		{"parenttype": "CRM Pipeline", "parent": pipeline, "stage": stage},
		["fieldname", "visible", "required", "read_only"],
	)
	return {
		r.fieldname: {"visible": r.visible, "required": r.required, "read_only": r.read_only} for r in rules
	}


def is_empty(df, value) -> bool:
	if df.fieldtype == "Check":
		return not value
	if df.fieldtype in NUMBER_TYPES:
		return value in (None, "") or not frappe.utils.flt(value)
	return value is None or (isinstance(value, str) and not value.strip())


def get_missing_fields(doc, stage: str) -> list[dict]:
	"""Required fields of `stage` that are empty on the card."""
	missing = []
	for fieldname, rule in get_stage_rules(doc.pipeline, stage).items():
		df = doc.meta.get_field(fieldname)
		if rule["required"] and df and is_empty(df, doc.get(fieldname)):
			missing.append(
				{
					"fieldname": fieldname,
					"label": _(df.label),
					"fieldtype": df.fieldtype,
					"options": df.options or "",
				}
			)
	return missing


def _normalize(df, value):
	if is_empty(df, value) and df.fieldtype not in NUMBER_TYPES:
		return None
	if df.fieldtype == "Date":
		return frappe.utils.getdate(value)
	if df.fieldtype in NUMBER_TYPES:
		return frappe.utils.flt(value)
	if df.fieldtype == "Check":
		return frappe.utils.cint(value)
	return frappe.utils.cstr(value)


def _changed(df, old, new) -> bool:
	return _normalize(df, old) != _normalize(df, new)


def validate_deal(doc):
	"""Card rules: entering a stage needs its required fields; read-only fields of the current stage
	cannot change. Applies to the UI and the API alike."""
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate or not doc.pipeline:
		return
	if doc.is_new() or doc.has_value_changed("status"):
		missing = get_missing_fields(doc, doc.status)
		if missing:
			frappe.local.response["missing_fields"] = missing
			frappe.throw(
				_("Fill in the required fields of this stage: {0}").format(
					", ".join(frappe.bold(m["label"]) for m in missing)
				),
				MissingRequiredFieldsError,
				title=_("Required fields"),
			)
	before = doc.get_doc_before_save()
	if not before or before.pipeline != doc.pipeline:
		return
	for fieldname, rule in get_stage_rules(doc.pipeline, before.status).items():
		df = doc.meta.get_field(fieldname)
		if rule["read_only"] and df and _changed(df, before.get(fieldname), doc.get(fieldname)):
			frappe.throw(
				_("{0} cannot be changed in this stage.").format(
					frappe.bold(_(df.label) if df else fieldname)
				)
			)
