# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Max

from crm.fcrm.doctype.crm_pipeline.fields import validate_pipeline_fields


class CRMPipeline(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_pipeline_field.crm_pipeline_field import CRMPipelineField
		from crm.fcrm.doctype.crm_pipeline_field_rule.crm_pipeline_field_rule import CRMPipelineFieldRule
		from crm.fcrm.doctype.crm_pipeline_member.crm_pipeline_member import CRMPipelineMember

		color: DF.Literal[
			"black",
			"gray",
			"blue",
			"green",
			"red",
			"pink",
			"orange",
			"amber",
			"yellow",
			"cyan",
			"teal",
			"violet",
			"purple",
		]
		field_rules: DF.Table[CRMPipelineFieldRule]
		fields: DF.Table[CRMPipelineField]
		icon: DF.Data | None
		is_active: DF.Check
		members: DF.Table[CRMPipelineMember]
		pipeline_name: DF.Data
		position: DF.Int
	# end: auto-generated types

	def validate(self):
		self.pipeline_name = (self.pipeline_name or "").strip()
		if not self.position:
			self.position = next_position("CRM Pipeline")
		self.validate_members()
		validate_pipeline_fields(self)

	def validate_members(self):
		seen = set()
		for member in self.members:
			if member.user in seen:
				frappe.throw(
					_("Row {0}: user {1} is already a member of this pipeline.").format(
						member.idx, frappe.bold(member.user)
					)
				)
			seen.add(member.user)
			if member.role == "Owner" and not can_own_pipelines(member.user):
				frappe.throw(
					_("Row {0}: give user {1} the Pipeline Owner role before making them an owner.").format(
						member.idx, frappe.bold(member.user)
					)
				)

	def on_trash(self):
		if frappe.db.exists("CRM Deal", {"pipeline": self.name}):
			frappe.throw(
				_("Pipeline {0} has cards. Move them to another pipeline before deleting it.").format(
					frappe.bold(self.pipeline_name)
				),
				frappe.LinkExistsError,
			)
		for view in frappe.get_all("CRM View Settings", {"pipeline": self.name}, pluck="name"):
			frappe.delete_doc("CRM View Settings", view, ignore_permissions=True)
		for stage in frappe.get_all("CRM Deal Status", {"pipeline": self.name}, pluck="name"):
			# force: this pipeline's own field rules still point at the stage until it is deleted
			frappe.delete_doc("CRM Deal Status", stage, ignore_permissions=True, force=True)


def add_members(pipeline: str, users: list[str], role: str = "Member"):
	"""Add users to a pipeline, keeping existing memberships as they are."""
	doc = frappe.get_doc("CRM Pipeline", pipeline)
	current = {m.user for m in doc.members}
	for user in users:
		if user and user not in current:
			doc.append("members", {"user": user, "role": role})
			current.add(user)
	doc.save(ignore_permissions=True)


def can_own_pipelines(user: str) -> bool:
	from crm.permissions.pipeline import PIPELINE_OWNER_ROLE, is_admin

	return is_admin(user) or PIPELINE_OWNER_ROLE in frappe.get_roles(user)


def next_position(doctype: str, **filters) -> int:
	"""Position after the last record of `doctype` matching `filters` (field == value)."""
	table = frappe.qb.DocType(doctype)
	query = frappe.qb.from_(table).select(Max(table.position))
	for field, value in filters.items():
		query = query.where(table[field] == value)
	return (query.run()[0][0] or 0) + 1


def get_default_pipeline(user: str | None = None) -> str | None:
	"""First active pipeline the user takes part in (any active one for admins). Only a suggestion
	for screens and forms: a card without a pipeline is refused, never placed here."""
	from crm.permissions.pipeline import is_admin

	user = user or frappe.session.user
	filters = {"is_active": 1}
	if not is_admin(user):
		Member = frappe.qb.DocType("CRM Pipeline Member")
		member_of = (
			frappe.qb.from_(Member)
			.select(Member.parent)
			.where((Member.parenttype == "CRM Pipeline") & (Member.user == user))
			.run(pluck=True)
		)
		if not member_of:
			return None
		filters["name"] = ("in", member_of)
	pipelines = frappe.get_all(
		"CRM Pipeline", filters, pluck="name", order_by="position asc, creation asc", limit=1
	)
	return pipelines[0] if pipelines else None


def get_first_stage(pipeline: str) -> str | None:
	"""First stage of a pipeline by position, preferring open stages over won/lost ones."""
	stages = frappe.get_all(
		"CRM Deal Status",
		{"pipeline": pipeline},
		["name", "type"],
		order_by="position asc, creation asc",
	)
	for stage in stages:
		if stage.type not in ("Won", "Lost"):
			return stage.name
	return stages[0].name if stages else None
