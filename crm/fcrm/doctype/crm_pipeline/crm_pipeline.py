# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Max


class CRMPipeline(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

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

	def on_trash(self):
		if frappe.db.exists("CRM Deal", {"pipeline": self.name}):
			frappe.throw(
				_("Pipeline {0} has cards. Move them to another pipeline before deleting it.").format(
					frappe.bold(self.pipeline_name)
				),
				frappe.LinkExistsError,
			)
		if frappe.db.get_single_value("FCRM Settings", "entry_pipeline") == self.name:
			frappe.throw(_("This is the entry pipeline. Choose another entry pipeline before deleting it."))
		for view in frappe.get_all("CRM View Settings", {"pipeline": self.name}, pluck="name"):
			frappe.delete_doc("CRM View Settings", view, ignore_permissions=True)
		for stage in frappe.get_all("CRM Deal Status", {"pipeline": self.name}, pluck="name"):
			frappe.delete_doc("CRM Deal Status", stage, ignore_permissions=True)


def next_position(doctype: str, **filters) -> int:
	"""Position after the last record of `doctype` matching `filters` (field == value)."""
	table = frappe.qb.DocType(doctype)
	query = frappe.qb.from_(table).select(Max(table.position))
	for field, value in filters.items():
		query = query.where(table[field] == value)
	return (query.run()[0][0] or 0) + 1


def get_default_pipeline() -> str | None:
	"""Pipeline used when a card is created without one: the entry pipeline, else the first active one."""
	entry = frappe.db.get_single_value("FCRM Settings", "entry_pipeline")
	if entry and frappe.db.get_value("CRM Pipeline", entry, "is_active"):
		return entry
	pipelines = frappe.get_all(
		"CRM Pipeline", {"is_active": 1}, pluck="name", order_by="position asc, creation asc", limit=1
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
