# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAPI4ComSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_token: DF.Password | None
		enabled: DF.Check
		webhook_secret: DF.Password | None
	# end: auto-generated types

	pass
