# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTelephonyAgent(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_telephony_extension.crm_telephony_extension import CRMTelephonyExtension
		from crm.fcrm.doctype.crm_telephony_phone.crm_telephony_phone import CRMTelephonyPhone

		call_receiving_device: DF.Literal["Computer", "Phone"]
		default_medium: DF.Literal["", "Twilio", "Exotel", "API4Com", "Nvoip"]
		exotel_number: DF.Data | None
		extensions: DF.Table[CRMTelephonyExtension]
		mobile_no: DF.Data | None
		phone_nos: DF.Table[CRMTelephonyPhone]
		twilio_number: DF.Data | None
		user: DF.Link
		user_name: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.update_phone_nos_based_on_mobile_no()
		self.set_primary()
		self.validate_extensions()

	def validate_extensions(self):
		"""One extension per operator for this user, and no other user with it at that operator:
		the extension is how a call finds its salesperson (credtech#268)."""
		from crm.integrations.voip.operators import get_operator_by_medium

		seen = set()
		for row in self.extensions:
			row.extension = (row.extension or "").strip()
			operator = get_operator_by_medium(row.medium)
			if not operator:
				frappe.throw(_("Unknown telephony operator: {0}").format(row.medium))
			if row.medium in seen:
				frappe.throw(_("{0} already has an extension for this user.").format(row.medium))
			seen.add(row.medium)
			operator.validate_extension(row.extension)
			owner = frappe.db.get_value(
				"CRM Telephony Extension",
				{
					"parenttype": "CRM Telephony Agent",
					"medium": row.medium,
					"extension": row.extension,
					"parent": ("!=", self.name or self.user),
				},
				"parent",
			)
			if owner:
				frappe.throw(_("Extension {0} already belongs to {1}.").format(row.extension, owner))

	def get_extension(self, medium: str) -> str | None:
		return next((row.extension for row in self.extensions if row.medium == medium), None)

	def set_extension(self, medium: str, extension: str | None):
		"""Empty removes the user's extension at that operator."""
		row = next((row for row in self.extensions if row.medium == medium), None)
		if not extension:
			if row:
				self.remove(row)
		elif row:
			row.extension = extension
		else:
			self.append("extensions", {"medium": medium, "extension": extension})

	def update_phone_nos_based_on_mobile_no(self):
		doc_before_save = self.get_doc_before_save()
		if not doc_before_save:
			return

		old_mobile_no = doc_before_save.mobile_no
		new_mobile_no = self.mobile_no

		if old_mobile_no == new_mobile_no:
			return

		# if new mobile no. is not in phone_nos table, then add it
		if new_mobile_no and not any(phone.get("number") == new_mobile_no for phone in self.phone_nos):
			self.append("phone_nos", {"number": new_mobile_no, "is_primary": 1})

		# if old mobile no. is in phone_nos table, then remove it
		phone_to_remove = next(
			(phone for phone in self.phone_nos if phone.get("number") == old_mobile_no), None
		)
		if phone_to_remove:
			self.phone_nos.remove(phone_to_remove)

	def set_primary(self):
		# Used to set primary mobile no.
		if not self.phone_nos and not self.mobile_no:
			return

		if not self.phone_nos:
			self.append("phone_nos", {"number": self.mobile_no, "is_primary": 1})

		primary_numbers = [phone.get("number") for phone in self.phone_nos if phone.get("is_primary")]

		if len(primary_numbers) > 1:
			frappe.throw(
				_("Only one {0} can be set as primary.").format(frappe.bold(frappe.unscrub("mobile_no")))
			)

		primary = next((d for d in self.phone_nos if d.get("is_primary") == 1), None)
		self.mobile_no = primary.get("number") if primary else ""
