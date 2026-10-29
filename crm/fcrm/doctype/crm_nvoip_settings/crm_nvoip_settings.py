# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMNvoipSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		enabled: DF.Check
		numbersip: DF.Data | None
		user_token: DF.Password | None
	# end: auto-generated types

	def validate(self):
		if not self.enabled:
			return
		if not (self.numbersip or "").strip():
			frappe.throw(_("Enter the Nvoip numbersip."))
		if not self.get_password("user_token", raise_exception=False):
			frappe.throw(_("Paste the Nvoip user-token."))
