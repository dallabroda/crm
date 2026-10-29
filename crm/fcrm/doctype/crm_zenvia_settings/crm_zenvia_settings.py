# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt
"""Zenvia Voz settings of the company (credtech#272).

The customer hires Zenvia directly and pastes here the access token of the voice panel. Zenvia has no API
to register webhooks on the company's own account, so the screen shows the two addresses to paste in the
Zenvia panel (Desenvolvedores > Configurações da API): "Chamada - Fim" and "DID - Fim de Chamada".
"""

import re

import frappe
from frappe import _
from frappe.model.document import Document


class CRMZenviaSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Password | None
		caller_number: DF.Data | None
		enabled: DF.Check
		webhook_secret: DF.Password | None
	# end: auto-generated types

	def validate(self):
		if not self.get_password("webhook_secret", raise_exception=False):
			self.webhook_secret = frappe.generate_hash(length=40)
		if not self.enabled:
			return
		if not self.get_password("access_token", raise_exception=False):
			frappe.throw(_("Paste the Zenvia access token."))
		# A token typed now comes in clear; one kept from before is asterisks (same as the API4Com settings)
		if self.access_token and not self.is_dummy_password(self.access_token):
			self.flags.check_token = True
		self.caller_number = re.sub(r"[^\d+]", "", self.caller_number or "")
		if self.caller_number and not re.fullmatch(r"\+[1-9]\d{7,14}", self.caller_number):
			frappe.throw(_("Enter the caller number in international format, e.g. +5548999990000."))

	def on_update(self):
		# A new token or turning it on: check it with Zenvia. A refusal rolls the save back.
		if self.enabled and (self.flags.check_token or self.has_value_changed("enabled")):
			from crm.integrations.voip.zenvia import check_token

			check_token(self)

	@frappe.whitelist()
	def get_webhook_urls(self):
		"""Shown only to who manages the settings; the secret goes in the addresses."""
		self.check_permission("write")
		from crm.integrations.voip.zenvia import webhook_urls

		return webhook_urls(self)

	@frappe.whitelist()
	def regenerate_webhook_secret(self):
		"""New secret: the old addresses stop working at once and must be pasted again in the Zenvia panel."""
		self.check_permission("write")
		self.webhook_secret = frappe.generate_hash(length=40)
		self.save()
