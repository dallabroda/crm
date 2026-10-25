# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline, next_position


class CRMDealStatus(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

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
		deal_status: DF.Data
		pipeline: DF.Link
		position: DF.Int
		probability: DF.Percent
		type: DF.Literal["Open", "Ongoing", "On Hold", "Won", "Lost"]
	# end: auto-generated types

	def validate(self):
		self.deal_status = (self.deal_status or "").strip()
		if not self.pipeline:
			self.pipeline = get_default_pipeline()
		self.validate_unique_in_pipeline()
		self.validate_pipeline_change()
		if not self.position:
			self.position = next_position("CRM Deal Status", pipeline=self.pipeline)

	def validate_unique_in_pipeline(self):
		# Stage names are unique per pipeline, not globally: two pipelines may both have "Qualification".
		duplicate = frappe.db.exists(
			"CRM Deal Status",
			{"pipeline": self.pipeline, "deal_status": self.deal_status, "name": ("!=", self.name)},
		)
		if duplicate:
			frappe.throw(
				_("Stage {0} already exists in this pipeline.").format(frappe.bold(self.deal_status)),
				frappe.DuplicateEntryError,
			)

	def validate_pipeline_change(self):
		if self.is_new() or not self.has_value_changed("pipeline"):
			return
		if frappe.db.exists("CRM Deal", {"status": self.name}):
			frappe.throw(_("A stage that has cards cannot be moved to another pipeline."))
