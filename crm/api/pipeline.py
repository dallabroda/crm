# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Pipelines (funis) API: pipelines, their stages and members, and moving cards between them.

Contract shared with the UI: credtech/docs/propostas/cred-hub-funis-divisao.md.
"""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_pipeline import distribution
from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage
from crm.fcrm.doctype.crm_pipeline.fields import default_pipeline_fields, sync_rules
from crm.permissions.pipeline import PIPELINE_OWNER_ROLE, get_role_in_pipeline, is_admin
from crm.utils.hidden_users import hidden_users

CRM_ROLES = ("Sales User", "Sales Manager", "System Manager")
STAGE_FIELDS = ("name", "deal_status", "color", "type", "position")
STAGE_TYPES = ("Open", "Ongoing", "On Hold", "Won", "Lost")


def _stages(pipeline: str) -> list[dict]:
	return frappe.get_all(
		"CRM Deal Status",
		{"pipeline": pipeline},
		list(STAGE_FIELDS),
		order_by="position asc, creation asc",
	)


def _assert_can_view(pipeline: str) -> str:
	role = get_role_in_pipeline(pipeline)
	if not role:
		frappe.throw(_("You are not a member of this pipeline."), frappe.PermissionError)
	return role


def _assert_can_manage(pipeline: str):
	if get_role_in_pipeline(pipeline) not in ("Admin", "Owner"):
		frappe.throw(_("Only pipeline owners can change this pipeline."), frappe.PermissionError)


@frappe.whitelist()
def get_pipelines(include_inactive: bool = False) -> list[dict]:
	"""Pipelines the user can see, ordered by position, each with its stages and the user's role."""
	include_inactive = frappe.utils.sbool(include_inactive) and is_admin()
	filters = {} if include_inactive else {"is_active": 1}
	pipelines = frappe.get_all(
		"CRM Pipeline",
		filters,
		["name", "pipeline_name", "color", "icon", "position", "is_active"],
		order_by="position asc, creation asc",
	)
	result = []
	for pipeline in pipelines:
		role = get_role_in_pipeline(pipeline.name)
		if not role:
			continue
		pipeline["my_role"] = role
		pipeline["stages"] = _stages(pipeline.name)
		result.append(pipeline)
	return result


@frappe.whitelist()
def get_pipeline_config(pipeline: str) -> dict:
	"""Full pipeline: stages, members, fields in use and per-stage field rules."""
	role = _assert_can_view(pipeline)
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	hidden = hidden_users()
	members = [m for m in doc.members if m.user not in hidden]
	users = [m.user for m in members]
	full_names = (
		dict(frappe.get_all("User", {"name": ("in", users)}, ["name", "full_name"], as_list=True))
		if users
		else {}
	)
	return {
		"name": doc.name,
		"pipeline_name": doc.pipeline_name,
		"color": doc.color,
		"icon": doc.icon,
		"position": doc.position,
		"is_active": doc.is_active,
		"my_role": role,
		"stages": _stages(doc.name),
		"distribution": distribution.load(doc.distribution),
		"members": [
			{"user": m.user, "full_name": full_names.get(m.user) or m.user, "role": m.role}
			for m in members
		],
		"fields": [{"fieldname": f.fieldname, "position": f.position} for f in doc.fields],
		"field_rules": [
			{
				"stage": r.stage,
				"fieldname": r.fieldname,
				"visible": r.visible,
				"required": r.required,
				"read_only": r.read_only,
			}
			for r in doc.field_rules
		],
	}


@frappe.whitelist()
def save_pipeline(doc: str | dict) -> dict:
	"""Create (no "name") or update a pipeline with its stages, members, fields and field rules,
	in one transaction. Keys left out of the payload are not touched.

	- stages: saved in the order received (position = order); existing stages missing from the
	  payload are deleted, which fails if a card is still in them.
	- fields: fieldnames from the catalog, in order (a new pipeline starts with the standard ones).
	- field_rules: {stage, fieldname, visible, required, read_only} for existing stages; any
	  (field, stage) pair not sent keeps its rule, new pairs start visible, optional and editable.
	"""
	data = frappe._dict(json.loads(doc) if isinstance(doc, str) else doc)
	if data.get("name"):
		_assert_can_manage(data.name)
		pipeline = frappe.get_doc("CRM Pipeline", data.name)
	else:
		if not is_admin() and PIPELINE_OWNER_ROLE not in frappe.get_roles():
			frappe.throw(_("Only pipeline owners can create pipelines."), frappe.PermissionError)
		pipeline = frappe.new_doc("CRM Pipeline")

	for key in ("pipeline_name", "color", "icon", "position", "is_active"):
		if key in data:
			pipeline.set(key, data[key])
	if "distribution" in data:
		# Who gets the cards that arrive on their own (credtech#51); unknown keys and incomplete rules dropped
		pipeline.distribution = json.dumps(distribution.normalize(data.distribution))

	if "members" in data:
		# Hidden users (API keys) are not on the screen, so saving the members keeps them as they were
		hidden = hidden_users()
		kept = [{"user": m.user, "role": m.role} for m in pipeline.members if m.user in hidden]
		pipeline.set("members", [])
		for member in data.members or []:
			if member.get("user") in hidden:
				continue
			pipeline.append("members", {"user": member.get("user"), "role": member.get("role") or "Member"})
		for member in kept:
			pipeline.append("members", member)

	creating = pipeline.is_new()
	if (
		creating
		and not is_admin()
		and not any(m.user == frappe.session.user and m.role == "Owner" for m in pipeline.members)
	):
		# Whoever creates a pipeline owns it, so they can keep managing it
		pipeline.append("members", {"user": frappe.session.user, "role": "Owner"})

	if "fields" in data or creating:
		fieldnames = (
			[f if isinstance(f, str) else f.get("fieldname") for f in data.fields or []]
			if "fields" in data
			else default_pipeline_fields()
		)
		pipeline.set("fields", [{"fieldname": f, "position": i} for i, f in enumerate(fieldnames, start=1)])

	pipeline.save(ignore_permissions=True)

	removed_stages = []
	if "stages" in data:
		removed_stages = _save_stages(pipeline.name, data.stages or [])

	stages = frappe.get_all(
		"CRM Deal Status",
		{"pipeline": pipeline.name, "name": ("not in", removed_stages or [""])},
		pluck="name",
		order_by="position asc, creation asc",
	)
	if "field_rules" in data:
		_apply_rules(pipeline, stages, data.field_rules or [])
	sync_rules(pipeline, stages)
	pipeline.save(ignore_permissions=True)

	for name in removed_stages:
		frappe.delete_doc("CRM Deal Status", name, ignore_permissions=True)

	return get_pipeline_config(pipeline.name)


def _apply_rules(pipeline, stages: list[str], rules: list[dict]):
	existing = {(r.stage, r.fieldname): r for r in pipeline.field_rules}
	used = {f.fieldname for f in pipeline.fields}
	for rule in rules:
		rule = frappe._dict(rule)
		if rule.stage not in stages:
			frappe.throw(_("Rule for an unknown stage: {0}").format(frappe.bold(rule.stage)))
		if rule.fieldname not in used:
			frappe.throw(_("Field {0} is not used in this pipeline.").format(frappe.bold(rule.fieldname)))
		row = existing.get((rule.stage, rule.fieldname))
		if not row:
			row = pipeline.append("field_rules", {"stage": rule.stage, "fieldname": rule.fieldname})
			existing[(rule.stage, rule.fieldname)] = row
		for key in ("visible", "required", "read_only"):
			if key in rule:
				row.set(key, frappe.utils.cint(rule[key]))


def _save_stages(pipeline: str, stages: list[dict]) -> list[str]:
	"""Create/update stages in order; returns the stages to delete (checked to have no cards)."""
	if not stages:
		frappe.throw(_("A pipeline needs at least one stage."))
	labels = [(s.get("deal_status") or "").strip() for s in stages if s.get("deal_status")]
	duplicates = {label for label in labels if labels.count(label) > 1}
	if duplicates:
		frappe.throw(
			_("Stage {0} appears more than once.").format(frappe.bold(", ".join(sorted(duplicates)))),
			frappe.DuplicateEntryError,
		)
	# Renames are applied one by one, so swapping two names would collide midway: park renamed stages
	# under their (unique) key first
	for stage in stages:
		if not stage.get("name"):
			continue
		current = frappe.db.get_value(
			"CRM Deal Status", stage["name"], ["pipeline", "deal_status"], as_dict=True
		)
		if not current:
			frappe.throw(
				_("Stage {0} not found.").format(frappe.bold(stage["name"])), frappe.DoesNotExistError
			)
		if current.pipeline != pipeline:
			frappe.throw(_("Stage {0} belongs to another pipeline.").format(frappe.bold(current.deal_status)))
		if stage.get("deal_status") and current.deal_status != stage["deal_status"].strip():
			frappe.db.set_value("CRM Deal Status", stage["name"], "deal_status", stage["name"])
	keep = set()
	for position, stage in enumerate(stages, start=1):
		stage = frappe._dict(stage)
		if stage.get("type") and stage.type not in STAGE_TYPES:
			frappe.throw(_("Invalid stage type: {0}").format(stage.type))
		if stage.get("name"):
			doc = frappe.get_doc("CRM Deal Status", stage.name)
			if doc.pipeline != pipeline:
				frappe.throw(_("Stage {0} belongs to another pipeline.").format(frappe.bold(doc.deal_status)))
		else:
			doc = frappe.new_doc("CRM Deal Status")
			doc.pipeline = pipeline
		for key in ("deal_status", "color", "type"):
			if key in stage:
				doc.set(key, stage[key])
		doc.position = position
		doc.save(ignore_permissions=True)
		keep.add(doc.name)

	removed = []
	for name in frappe.get_all("CRM Deal Status", {"pipeline": pipeline}, pluck="name"):
		if name in keep:
			continue
		if frappe.db.exists("CRM Deal", {"status": name}):
			label = frappe.db.get_value("CRM Deal Status", name, "deal_status")
			frappe.throw(
				_("Stage {0} still has cards. Move them before removing the stage.").format(
					frappe.bold(label)
				)
			)
		removed.append(name)
	return removed


@frappe.whitelist()
def get_pipeline_users() -> dict:
	"""Active CRM users for the pipeline members screen, with who may own pipelines."""
	frappe.only_for(CRM_ROLES)
	users = frappe.get_all(
		"User",
		{
			"enabled": 1,
			"name": ("not in", ("Administrator", "Guest")),
			"user_type": "System User",
		},
		["name", "full_name", "user_image"],
		order_by="full_name asc",
	)
	result = []
	hidden = hidden_users()
	for user in users:
		roles = set(frappe.get_roles(user.name))
		if not roles & set(CRM_ROLES) or user.name in hidden:
			continue
		admin = is_admin(user.name)
		result.append(
			{
				**user,
				"pipeline_owner": int(admin or PIPELINE_OWNER_ROLE in roles),
				"is_admin": int(admin),
			}
		)
	return {
		"can_create": int(is_admin() or PIPELINE_OWNER_ROLE in frappe.get_roles()),
		"is_admin": int(is_admin()),
		"users": result,
	}


@frappe.whitelist()
def set_pipeline_owner_role(user: str, enabled: bool) -> dict:
	"""Give or take the global Pipeline Owner role (create pipelines, be an owner). Admins only."""
	if not is_admin():
		frappe.throw(_("Only admins can change who owns pipelines."), frappe.PermissionError)
	doc = frappe.get_doc("User", user)
	# Sales Managers manage this role without having write access to User itself
	doc.flags.ignore_permissions = True
	if frappe.utils.sbool(enabled):
		doc.add_roles(PIPELINE_OWNER_ROLE)
	else:
		owned = frappe.get_all(
			"CRM Pipeline Member",
			{"parenttype": "CRM Pipeline", "user": user, "role": "Owner"},
			pluck="parent",
		)
		if owned:
			frappe.throw(
				_("{0} still owns pipelines. Change them to member first.").format(frappe.bold(user))
			)
		doc.remove_roles(PIPELINE_OWNER_ROLE)
	return {"user": user, "pipeline_owner": PIPELINE_OWNER_ROLE in frappe.get_roles(user)}


@frappe.whitelist()
def move_card(deal: str, stage: str, values: str | dict | None = None) -> dict:
	"""Move a card to another stage of its pipeline, optionally filling fields at the same time."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("write")
	_set_values(doc, values)
	doc.status = stage
	doc.save()
	return doc.as_dict()


@frappe.whitelist()
def change_pipeline(deal: str, pipeline: str, stage: str | None = None) -> dict:
	"""Move a card to another pipeline (first stage unless one is given). Field values are kept."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("write")
	_assert_can_view(pipeline)
	doc.pipeline = pipeline
	doc.status = stage or get_first_stage(pipeline)
	doc.save()
	return doc.as_dict()


def _set_values(doc, values):
	if not values:
		return
	values = json.loads(values) if isinstance(values, str) else values
	protected = {"name", "pipeline", "status", "owner", "creation", "modified", "doctype"}
	for fieldname, value in values.items():
		df = doc.meta.get_field(fieldname)
		if (
			fieldname in protected
			or not df
			or df.read_only
			or df.fieldtype in frappe.model.table_fields
			or not doc.has_permlevel_access_to(fieldname, df, "write")
		):
			frappe.throw(_("Field {0} cannot be set here.").format(frappe.bold(fieldname)))
		doc.set(fieldname, value)


@frappe.whitelist()
def get_stage_rules(pipeline: str, stage: str) -> dict:
	"""{fieldname: {visible, required, read_only}} for the fields used in the pipeline, in `stage`."""
	_assert_can_view(pipeline)
	return field_catalog.get_stage_rules(pipeline, stage)


@frappe.whitelist()
def get_missing_fields(deal: str, stage: str) -> list[dict]:
	"""Required fields of `stage` that are empty on the card (what to ask before moving it)."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("read")
	return field_catalog.get_missing_fields(doc, stage)


@frappe.whitelist()
def get_field_catalog() -> dict:
	frappe.only_for(CRM_ROLES)
	return {
		"limit": field_catalog.CREATED_FIELD_LIMIT,
		"used": field_catalog.created_field_count(),
		# how many more fields of each type still fit in the cards table (text runs out first)
		"room": field_catalog.room_by_type(),
		"fields": field_catalog.get_catalog(),
		# card fields that moved to the organization: left out of the card's screens, still usable in
		# distribution rules (they test the incoming lead)
		"moved": [
			field_catalog._field_info(df, True)
			for df in (
				frappe.get_meta(field_catalog.DEAL).get_field(f) for f in field_catalog.MOVED_TO_ORGANIZATION
			)
			if df
		],
	}


def _assert_admin():
	if not is_admin():
		frappe.throw(_("Only admins can change the field catalog."), frappe.PermissionError)


@frappe.whitelist()
def create_field(label: str, fieldtype: str, options: str | None = None) -> dict:
	_assert_admin()
	return field_catalog.create_field(label, fieldtype, options)


@frappe.whitelist()
def update_field(fieldname: str, label: str | None = None, options: str | None = None) -> dict:
	_assert_admin()
	return field_catalog.update_field(fieldname, label, options)


@frappe.whitelist()
def disable_field(fieldname: str) -> dict:
	_assert_admin()
	return field_catalog.disable_field(fieldname)
