# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMNvoipPendingCall(Document):
	"""A Nvoip click-to-call waiting for its outcome (credtech#269): Nvoip's own `POST /calls/`
	does not take a custom field, so the deal travels here instead, keyed by the `callId` Nvoip
	gave us, until the poller reads the call's final state and records it."""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		call_id: DF.Data
		deal: DF.Link | None
		extension: DF.Data
		number: DF.Data
	# end: auto-generated types

	pass
