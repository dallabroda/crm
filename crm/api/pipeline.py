# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Pipelines (funis) API: pipelines, their stages and members, and moving cards between them.

Contract shared with the UI: credtech/docs/propostas/cred-hub-funis-divisao.md.
"""

import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_first_stage

ADMIN_ROLES = ("System Manager", "Sales Manager")
STAGE_FIELDS = ("name", "deal_status", "color", "type", "position", "probability")
STAGE_TYPES = ("Open", "Ongoing", "On Hold", "Won", "Lost")


def is_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or bool(set(frappe.get_roles(user)) & set(ADMIN_ROLES))


def get_role_in_pipeline(pipeline: str, user: str | None = None) -> str | None:
	"""Admin, Owner or Member; None when the user does not take part in the pipeline."""
	user = user or frappe.session.user
	if is_admin(user):
		return "Admin"
	return frappe.db.get_value(
		"CRM Pipeline Member", {"parenttype": "CRM Pipeline", "parent": pipeline, "user": user}, "role"
	)


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
		if not frappe.has_permission("CRM Pipeline", "create"):
			frappe.throw(_("You are not allowed to create pipelines."), frappe.PermissionError)
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
		if fieldname in protected or not doc.meta.has_field(fieldname):
			frappe.throw(_("Field {0} cannot be set here.").format(frappe.bold(fieldname)))
		doc.set(fieldname, value)
