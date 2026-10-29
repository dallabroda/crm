# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt
"""Telnyx settings of the company (credtech#270).

The customer hires Telnyx directly, creates a Call Control Application and pastes here its API key, the
application's ID, the number shown to the customer and the account's webhook public key. Each call the CRM
places tells Telnyx where to send its webhooks, so nothing has to be configured on the application.
"""

import base64
import binascii
import re

import frappe
from frappe import _
from frappe.model.document import Document


class CRMTelnyxSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_key: DF.Password | None
		caller_number: DF.Data | None
		connection_id: DF.Data | None
		enabled: DF.Check
		public_key: DF.Data | None
		webhook_secret: DF.Password | None
	# end: auto-generated types

	def validate(self):
		if not self.get_password("webhook_secret", raise_exception=False):
			self.webhook_secret = frappe.generate_hash(length=40)
		if not self.enabled:
			return
		if not self.get_password("api_key", raise_exception=False):
			frappe.throw(_("Paste the Telnyx API key."))
		# A key typed now comes in clear; one kept from before is asterisks. Seen here, because the save masks
		# it before on_update (same as the API4Com settings).
		if self.api_key and not self.is_dummy_password(self.api_key):
			self.flags.check_application = True
		self.connection_id = (self.connection_id or "").strip()
		if not self.connection_id:
			frappe.throw(_("Enter the ID of the Telnyx Call Control Application."))
		self.caller_number = re.sub(r"[^\d+]", "", self.caller_number or "")
		if not re.fullmatch(r"\+[1-9]\d{7,14}", self.caller_number):
			frappe.throw(_("Enter the caller number in international format, e.g. +5548999990000."))
		self.public_key = (self.public_key or "").strip()
		try:
			valid_key = len(base64.b64decode(self.public_key, validate=True)) == 32
		except (ValueError, binascii.Error):
			valid_key = False
		if not valid_key:
			frappe.throw(
				_("Paste the Telnyx public key as shown in the portal (Keys & Credentials > Public Key).")
			)

	def on_update(self):
		# A new key, another application or turning it on: check them with Telnyx. A refusal rolls the save back.
		changed = self.flags.check_application or any(
			self.has_value_changed(field) for field in ("enabled", "connection_id")
		)
		if self.enabled and changed:
			check_application(self)


def check_application(settings):
	"""GET /call_control_applications/{id}: the key works and the application exists."""
	from crm.integrations.voip.telnyx import _request

	response = _request(settings, "get", f"/call_control_applications/{settings.connection_id}")
	if response.status_code == 401:
		frappe.throw(_("Telnyx refused the API key. Check that it was copied whole."))
	if response.status_code == 404:
		frappe.throw(_("Telnyx did not find a Call Control Application with this ID."))
	if response.status_code >= 400:
		frappe.throw(_("Telnyx refused the settings (HTTP {0}).").format(response.status_code))
