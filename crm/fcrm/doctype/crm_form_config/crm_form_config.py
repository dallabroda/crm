# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMFormConfig(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_form_field.crm_form_field import CRMFormField

		fields: DF.Table[CRMFormField]
		form_doctype: DF.Link
	# end: auto-generated types

	pass
