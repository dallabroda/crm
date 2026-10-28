# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Company field catalog for cards and the per-stage rules (visible / required / read only)."""

import re
import unicodedata

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

DEAL = "CRM Deal"
# Doctypes whose forms the company configures (dynamic forms, credtech#178): cards, contacts and companies
FORM_DOCTYPES = (DEAL, "Contact", "CRM Organization")
# Created fields get this prefix, so they are told apart from standard and app fields
CREATED_PREFIX = "ch_"
CREATED_FIELD_LIMIT = 60
# Always shown and editable: a card cannot exist without them
LOCKED_FIELDS = ("pipeline", "status", "deal_owner")
STANDARD_FIELDS = (
	"organization",
	# offered in every funnel, but a funnel uses it only when someone adds it (credtech#195)
	"second_organization",
	"deal_value",
	"expected_closure_date",
	"next_step",
	"source",
)
# Owner decision 7 of 28/10/2026 (credtech#181): these belong to the organization, not to the card. The card
# columns stay (old values, lead conversion), but the card form no longer offers them.
MOVED_TO_ORGANIZATION = ("website", "annual_revenue", "no_of_employees", "industry")
FIELD_TYPES = ("Data", "Int", "Float", "Currency", "Date", "Select", "Check", "Attach", "Link")
LINK_TARGETS = ("Contact", "CRM Organization")
NUMBER_TYPES = ("Int", "Float", "Currency", "Percent")


# Blocks of the card form (credtech#196): the card's own fields, or fields of the records linked to it. The
# stage decides which of them show and are required; a block without a linked record is skipped.
CARD, ORGANIZATION, SECOND_ORGANIZATION, CONTACT = "Card", "Organization", "Second organization", "Contact"
BLOCKS = (CARD, ORGANIZATION, SECOND_ORGANIZATION, CONTACT)
BLOCK_DOCTYPES = {
	CARD: DEAL,
	ORGANIZATION: "CRM Organization",
	SECOND_ORGANIZATION: "CRM Organization",
	CONTACT: "Contact",
}


def block_of(row) -> str:
	return row.get("block") or CARD


def block_record(doc, block: str) -> str | None:
	"""The record a block of the card points at: the card, its organization, its second organization or its
	primary contact."""
	if block == CARD:
		return doc.name
	if block == ORGANIZATION:
		return doc.get("organization")
	if block == SECOND_ORGANIZATION:
		return doc.get("second_organization")
	primary = next((c.contact for c in doc.get("contacts") or [] if c.is_primary), None)
	return primary or next((c.contact for c in doc.get("contacts") or []), None) or doc.get("contact")


class MissingRequiredFieldsError(frappe.ValidationError):
	pass


class NoRoomForFieldError(frappe.ValidationError):
	pass


# MariaDB refuses a table whose columns add up to more than 65,535 bytes per row (error 1118). Cards already
# declare ~28 KB and each text field takes 562 bytes (140 characters in utf8mb4): in a test the 67th text field
# failed. CREATED_FIELD_LIMIT (60, owner decision) stays below that, but fields added by apps also take room, so
# the size is still checked. Numbers, dates and Yes/No take a few bytes.
ROW_SIZE_LIMIT = 65_535
ROW_SIZE_MARGIN = 256

# Same per-column sizes as frappe.db.get_row_size, but for this site's database only: that query does not
# filter by schema, so on a server with one database per company it adds up the tables of every company.
_ROW_SIZE_SQL = """
	SELECT COALESCE(SUM(CASE DATA_TYPE
		WHEN 'tinyint' THEN 1 WHEN 'smallint' THEN 2 WHEN 'mediumint' THEN 3 WHEN 'int' THEN 4
		WHEN 'bigint' THEN 8 WHEN 'float' THEN IF(NUMERIC_PRECISION > 24, 8, 4) WHEN 'double' THEN 8
		WHEN 'decimal' THEN ((NUMERIC_PRECISION - NUMERIC_SCALE) DIV 9) * 4 + (NUMERIC_SCALE DIV 9) * 4
			+ CEIL(MOD(NUMERIC_PRECISION - NUMERIC_SCALE, 9) / 2) + CEIL(MOD(NUMERIC_SCALE, 9) / 2)
		WHEN 'year' THEN 1 WHEN 'date' THEN 3
		WHEN 'time' THEN 3 + CEIL(DATETIME_PRECISION / 2)
		WHEN 'datetime' THEN 5 + CEIL(DATETIME_PRECISION / 2)
		WHEN 'timestamp' THEN 4 + CEIL(DATETIME_PRECISION / 2)
		WHEN 'char' THEN CHARACTER_OCTET_LENGTH
		WHEN 'varchar' THEN IF(CHARACTER_OCTET_LENGTH > 255, 2, 1) + CHARACTER_OCTET_LENGTH
		WHEN 'tinytext' THEN 9 WHEN 'text' THEN 10 WHEN 'mediumtext' THEN 11 WHEN 'longtext' THEN 12
		WHEN 'tinyblob' THEN 9 WHEN 'blob' THEN 10 WHEN 'mediumblob' THEN 11 WHEN 'longblob' THEN 12
		WHEN 'json' THEN 12 ELSE 8 END), 0)
	FROM information_schema.COLUMNS
	WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
"""


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


def _form_doctype(doctype: str) -> str:
	if doctype not in FORM_DOCTYPES:
		frappe.throw(_("Fields can only be created for cards, contacts and companies."))
	return doctype


def created_field_count(doctype: str = DEAL) -> int:
	return frappe.db.count("Custom Field", {"dt": doctype, "fieldname": ("like", f"{CREATED_PREFIX}%")})


def row_size(doctype: str = DEAL) -> int:
	"""Bytes the table already declares per row (this site's database)."""
	if frappe.db.db_type != "mariadb":
		return 0
	return int(frappe.db.sql(_ROW_SIZE_SQL, (f"tab{doctype}",))[0][0] or 0)


def field_cost(fieldtype: str) -> int:
	"""Bytes a new column of `fieldtype` adds to the row, from the column type Frappe gives it."""
	column, length = frappe.db.type_map.get(fieldtype, ("varchar", frappe.db.VARCHAR_LEN))
	if column == "varchar":
		octets = int(length or frappe.db.VARCHAR_LEN) * 4
		return octets + (2 if octets > 255 else 1)
	if column == "decimal":
		precision, scale = (int(x) for x in str(length or "21,9").split(","))
		whole = precision - scale
		return (whole // 9) * 4 + (scale // 9) * 4 + -(-(whole % 9) // 2) + -(-(scale % 9) // 2)
	return {"tinyint": 1, "int": 4, "bigint": 8, "date": 3, "datetime": 8, "time": 6}.get(column, 12)


def room_by_type(doctype: str = DEAL) -> dict:
	"""How many more fields of each creatable type still fit: the row size and the created-field limit."""
	left_by_count = max(CREATED_FIELD_LIMIT - created_field_count(doctype), 0)
	free = ROW_SIZE_LIMIT - ROW_SIZE_MARGIN - row_size(doctype)
	return {t: max(min(left_by_count, free // field_cost(t)), 0) for t in FIELD_TYPES}


def _no_room_message(fieldtype: str, doctype: str = DEAL) -> str:
	if doctype != DEAL:
		return _("There is no room left for another field of this type in {0}.").format(_(doctype))
	if fieldtype in ("Data", "Select", "Link"):
		return _(
			"There is no room left for another text, list or link field in cards. "
			"Number, date and Yes/No fields take much less space and can still be created."
		)
	return _("There is no room left for another field of this type in cards.")


def _is_row_size_error(e: Exception) -> bool:
	return bool(getattr(e, "args", None)) and e.args[0] == 1118


def create_field(label: str, fieldtype: str, options: str | None = None, doctype: str = DEAL) -> dict:
	doctype = _form_doctype(doctype)
	label = (label or "").strip()
	if not label:
		frappe.throw(_("Give the field a name."))
	if fieldtype not in FIELD_TYPES:
		frappe.throw(_("Field type {0} is not supported.").format(frappe.bold(fieldtype)))
	if created_field_count(doctype) >= CREATED_FIELD_LIMIT:
		frappe.throw(_("The limit of {0} created fields was reached.").format(CREATED_FIELD_LIMIT))
	if row_size(doctype) + field_cost(fieldtype) > ROW_SIZE_LIMIT - ROW_SIZE_MARGIN:
		frappe.throw(
			_no_room_message(fieldtype, doctype), NoRoomForFieldError, title=_("No room for this field")
		)
	options = _clean_options(fieldtype, options)

	base = fieldname_base(label)
	fieldname, n = base, 1
	meta = frappe.get_meta(doctype)
	while meta.has_field(fieldname) or frappe.db.exists(
		"Custom Field", {"dt": doctype, "fieldname": fieldname}
	):
		n += 1
		fieldname = f"{base}_{n}"

	try:
		create_custom_field(
			doctype,
			{
				"fieldname": fieldname,
				"label": label,
				"fieldtype": fieldtype,
				"options": options,
				"insert_after": _last_fieldname(doctype),
			},
			ignore_validate=False,
		)
	except frappe.db.OperationalError as e:
		# The estimate above can miss by a few bytes: never show the raw database error
		if not _is_row_size_error(e):
			raise
		# ALTER TABLE commits implicitly before it runs, so the Custom Field row was already saved:
		# remove it, or the cards would point to a column that does not exist
		frappe.db.rollback()
		frappe.db.delete("Custom Field", {"dt": doctype, "fieldname": fieldname})
		frappe.db.commit()
		frappe.clear_cache(doctype=doctype)
		frappe.throw(
			_no_room_message(fieldtype, doctype), NoRoomForFieldError, title=_("No room for this field")
		)
	frappe.clear_cache(doctype=doctype)
	return _catalog_item(fieldname, doctype)


def update_field(
	fieldname: str, label: str | None = None, options: str | None = None, doctype: str = DEAL
) -> dict:
	doctype = _form_doctype(doctype)
	cf = _created_custom_field(fieldname, doctype)
	if label is not None:
		label = label.strip()
		if not label:
			frappe.throw(_("Give the field a name."))
		cf.label = label
	if options is not None:
		cf.options = _clean_options(cf.fieldtype, options)
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)
	return _catalog_item(cf.fieldname, doctype)


def disable_field(fieldname: str, doctype: str = DEAL) -> dict:
	"""Hide a created field everywhere; its column and values are kept."""
	doctype = _form_doctype(doctype)
	cf = _created_custom_field(fieldname, doctype)
	cf.hidden = 1
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)
	# The lookup ignores accents (database collation): answer with the field actually found
	return _catalog_item(cf.fieldname, doctype)


def fieldname_base(label: str) -> str:
	"""ch_ + the name without accents, lowercase, letters and digits joined by _ ("CPF/CNPJ" -> ch_cpf_cnpj).
	frappe.scrub kept accents and symbols: "Renda (R$)" was refused and "Situação" made a column with accents."""
	plain = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
	slug = re.sub(r"[^a-z0-9]+", "_", plain.lower()).strip("_")[:50].rstrip("_")
	return CREATED_PREFIX + (slug or "field")


def _created_custom_field(fieldname: str, doctype: str = DEAL):
	if not (fieldname or "").startswith(CREATED_PREFIX):
		frappe.throw(_("Only fields created by the company can be changed."))
	name = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname})
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


def _last_fieldname(doctype: str = DEAL) -> str:
	fields = [df.fieldname for df in frappe.get_meta(doctype).fields]
	return fields[-1] if fields else "status"


def _catalog_item(fieldname: str, doctype: str = DEAL) -> dict:
	if doctype == DEAL:
		return next(f for f in get_catalog() if f["fieldname"] == fieldname)
	return _field_info(frappe.get_meta(doctype).get_field(fieldname), False)


# Rules ---------------------------------------------------------------------


def default_pipeline_fields() -> list[str]:
	"""Fields a new pipeline starts with: the standard ones."""
	meta = frappe.get_meta(DEAL)
	return [f for f in STANDARD_FIELDS if meta.has_field(f) and f != "second_organization"]


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
	used = [(block_of(f), f.fieldname) for f in pipeline_doc.fields]
	existing = {(r.stage, block_of(r), r.fieldname): r for r in pipeline_doc.field_rules}
	rows = []
	for stage in stages:
		for block, fieldname in used:
			rule = existing.get((stage, block, fieldname))
			rows.append(
				{
					"stage": stage,
					"block": block,
					"fieldname": fieldname,
					"visible": rule.visible if rule else 1,
					"required": rule.required if rule else 0,
					# fields of the linked records are only shown or required on the card, never read only
					"read_only": (rule.read_only if rule else 0) if block == CARD else 0,
				}
			)
	pipeline_doc.set("field_rules", rows)


def validate_pipeline_fields(pipeline_doc):
	"""New fields must come from the catalog. Fields already in the pipeline stay even if disabled
	(values are kept); fields that no longer exist at all are dropped with their rules."""
	before = pipeline_doc.get_doc_before_save()
	already_used = {(block_of(row), row.fieldname) for row in before.fields} if before else set()
	gone = {(b, f) for b, f in already_used if not frappe.get_meta(BLOCK_DOCTYPES.get(b, DEAL)).has_field(f)}
	if gone:
		pipeline_doc.set("fields", [r for r in pipeline_doc.fields if (block_of(r), r.fieldname) not in gone])
		pipeline_doc.set(
			"field_rules", [r for r in pipeline_doc.field_rules if (block_of(r), r.fieldname) not in gone]
		)

	available = catalog_fieldnames() | {f for b, f in already_used - gone if b == CARD}
	seen = set()
	for row in pipeline_doc.fields:
		block = block_of(row)
		if block not in BLOCKS:
			frappe.throw(_("Unknown block {0}.").format(frappe.bold(block)))
		if block != CARD:
			_validate_block_field(row, block)
			if (block, row.fieldname) in seen:
				frappe.throw(_("Field {0} was added twice.").format(frappe.bold(row.fieldname)))
			seen.add((block, row.fieldname))
			continue
		if row.fieldname in LOCKED_FIELDS:
			frappe.throw(
				_("{0} is always shown and does not need to be added.").format(frappe.bold(row.fieldname))
			)
		if row.fieldname not in available:
			frappe.throw(_("Field {0} is not in the field catalog.").format(frappe.bold(row.fieldname)))
		if (CARD, row.fieldname) in seen:
			frappe.throw(_("Field {0} was added twice.").format(frappe.bold(row.fieldname)))
		seen.add((CARD, row.fieldname))
	for rule in pipeline_doc.field_rules:
		if rule.required and not rule.visible:
			frappe.throw(_("A required field must be visible ({0}).").format(frappe.bold(rule.fieldname)))
		if rule.required and block_of(rule) != CARD:
			from crm.fcrm.doctype.crm_pipeline.form_schema import can_require

			doctype = BLOCK_DOCTYPES[block_of(rule)]
			df = frappe.get_meta(doctype).get_field(rule.fieldname)
			if df and not can_require(doctype, df):
				frappe.throw(
					_("{0} is filled in by the system and cannot be required.").format(frappe.bold(_(df.label)))
				)


def _validate_block_field(row, block: str):
	"""A field of a linked record must be in that record's form and be one a person fills in."""
	from crm.fcrm.doctype.crm_pipeline import form_schema

	doctype = BLOCK_DOCTYPES[block]
	field = next(
		(f for f in form_schema.form_catalog(doctype) if f["fieldname"] == row.fieldname and not f["disabled"]),
		None,
	)
	if not field or field["locked"]:
		frappe.throw(_("Field {0} is not in the {1} form.").format(frappe.bold(row.fieldname), _(block)))


def get_stage_rules(pipeline: str, stage: str, block: str = CARD) -> dict:
	rules = frappe.get_all(
		"CRM Pipeline Field Rule",
		{"parenttype": "CRM Pipeline", "parent": pipeline, "stage": stage},
		["block", "fieldname", "visible", "required", "read_only"],
	)
	return {
		r.fieldname: {"visible": r.visible, "required": r.required, "read_only": r.read_only}
		for r in rules
		if block_of(r) == block
	}


def is_empty(df, value) -> bool:
	if df.fieldtype == "Check":
		return not value
	if df.fieldtype in NUMBER_TYPES:
		return value in (None, "") or not frappe.utils.flt(value)
	return value is None or (isinstance(value, str) and not value.strip())


def get_missing_fields(doc, stage: str) -> list[dict]:
	"""Required fields of `stage` that are empty on the card and on the records linked to it (its
	organization, second organization and primary contact; a block without a record is skipped)."""
	missing = []
	for block in BLOCKS:
		rules = {f: r for f, r in get_stage_rules(doc.pipeline, stage, block).items() if r["required"]}
		record = block_record(doc, block)
		if not rules or not record:
			continue
		doctype = BLOCK_DOCTYPES[block]
		meta = frappe.get_meta(doctype)
		values = doc if block == CARD else frappe.db.get_value(doctype, record, list(rules), as_dict=True) or {}
		for fieldname in rules:
			df = meta.get_field(fieldname)
			if df and is_empty(df, values.get(fieldname)):
				missing.append(
					{
						"fieldname": fieldname,
						"label": _(df.label),
						"fieldtype": df.fieldtype,
						"options": df.options or "",
						"block": block,
						"doctype": doctype,
						"docname": record,
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
	automatic_entry = doc.is_new() and frappe.flags.get("crm_automatic_entry")
	if (doc.is_new() or doc.has_value_changed("status")) and not automatic_entry:
		missing = get_missing_fields(doc, doc.status)
		if missing:
			# frappe-ui only keeps `message` and the server messages on errors
			frappe.local.response["missing_fields"] = missing
			frappe.local.response["message"] = {"missing_fields": missing}
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
	moving = before.status != doc.status
	for fieldname, rule in get_stage_rules(doc.pipeline, before.status).items():
		df = doc.meta.get_field(fieldname)
		if not rule["read_only"] or not df:
			continue
		# Filling an empty field while moving on is allowed: the next stage may require it
		if moving and is_empty(df, before.get(fieldname)):
			continue
		if _changed(df, before.get(fieldname), doc.get(fieldname)):
			frappe.throw(
				_("{0} cannot be changed in this stage.").format(
					frappe.bold(_(df.label) if df else fieldname)
				)
			)
