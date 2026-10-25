# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Pipelines (funis) API: pipelines, their stages and members, and moving cards between them.

Contract shared with the UI: credtech/docs/propostas/cred-hub-funis-divisao.md.
"""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage
from crm.permissions.pipeline import PIPELINE_OWNER_ROLE, get_role_in_pipeline, is_admin

STAGE_FIELDS = ("name", "deal_status", "color", "type", "position", "probability")
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
	users = [m.user for m in doc.members]
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
		"members": [
			{"user": m.user, "full_name": full_names.get(m.user) or m.user, "role": m.role}
			for m in doc.members
		],
		# Fields and per-stage rules come with the field catalog (#69)
		"fields": [],
		"field_rules": [],
	}


@frappe.whitelist()
def save_pipeline(doc: str | dict) -> dict:
	"""Create (no "name") or update a pipeline with its stages and members, in one transaction.

	Stages are saved in the order received (position = order); existing stages missing from the
	payload are deleted, which fails if a card is still in them.
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

	if "members" in data:
		pipeline.set("members", [])
		for member in data.members or []:
			pipeline.append("members", {"user": member.get("user"), "role": member.get("role") or "Member"})

	creating = pipeline.is_new()
	if (
		creating
		and not is_admin()
		and not any(m.user == frappe.session.user and m.role == "Owner" for m in pipeline.members)
	):
		# Whoever creates a pipeline owns it, so they can keep managing it
		pipeline.append("members", {"user": frappe.session.user, "role": "Owner"})

	pipeline.save(ignore_permissions=True)

	if "stages" in data:
		_save_stages(pipeline.name, data.stages or [])

	return get_pipeline_config(pipeline.name)


def _save_stages(pipeline: str, stages: list[dict]):
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
		for key in ("deal_status", "color", "type", "probability"):
			if key in stage:
				doc.set(key, stage[key])
		doc.position = position
		doc.save(ignore_permissions=True)
		keep.add(doc.name)

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
		frappe.delete_doc("CRM Deal Status", name, ignore_permissions=True)


@frappe.whitelist()
def get_pipeline_users() -> dict:
	"""Active CRM users for the pipeline members screen, with who may own pipelines."""
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
	crm_roles = ("Sales User", "Sales Manager", "System Manager")
	result = []
	for user in users:
		roles = set(frappe.get_roles(user.name))
		if not roles & set(crm_roles):
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
