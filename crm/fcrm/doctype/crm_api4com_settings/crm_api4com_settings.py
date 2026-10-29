# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt
"""API4Com settings of the company (credtech#98).

The customer hires API4Com directly and pastes the API token here; the CRM generates the webhook
secret and registers its own webhook at API4Com, so the customer copies no URL. Token and secret
are Password fields: they never come back to the screen.
"""

import frappe
import requests
from frappe import _
from frappe.model.document import Document

from crm.integrations.voip.api4com import API_URL, GATEWAY

WEBHOOK_PATH = "/api/method/crm.integrations.voip.webhook.api4com"
WEBHOOK_VERSION = "v1.4"


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

	def validate(self):
		if not self.enabled:
			return
		if not self.get_password("api_token", raise_exception=False):
			frappe.throw(_("Paste the API4Com API token."))
		# A token typed now comes in clear; one kept from before is asterisks. Seen here, because the save
		# masks it before on_update, and a new token as long as the old one would not count as changed there.
		if self.api_token and not self.is_dummy_password(self.api_token):
			self.flags.register_webhook = True
		if not self.get_password("webhook_secret", raise_exception=False):
			self.webhook_secret = new_secret()
			self.flags.register_webhook = True

	def on_update(self):
		# A new token, turning it on or a new secret: (re)register the webhook. A refusal rolls the save back.
		if self.enabled and (self.flags.register_webhook or self.has_value_changed("enabled")):
			register_webhook(self)

	@frappe.whitelist()
	def regenerate_webhook_secret(self):
		"""New secret (the old URL stops working at once) and the webhook registered again."""
		self.check_permission("write")
		self.webhook_secret = new_secret()
		self.flags.register_webhook = True
		self.save()

	@frappe.whitelist()
	def get_webhook_url(self):
		"""Shown only to who manages the settings; the secret goes in the URL."""
		self.check_permission("write")
		return webhook_url(self)


def new_secret():
	return frappe.generate_hash(length=40)


def webhook_url(settings):
	secret = settings.get_password("webhook_secret", raise_exception=False)
	if not secret:
		return None
	return frappe.utils.get_url(f"{WEBHOOK_PATH}?key={secret}")


def register_webhook(settings):
	"""PATCH /integrations at API4Com (https://developers.api4com.com/integration-own-webphone.html).
	Not yet run against the real API: needs the test account of credtech#100."""
	try:
		response = requests.patch(
			f"{API_URL}/integrations",
			json={
				"gateway": GATEWAY,
				"webhook": True,
				"metadata": {
					"webhookUrl": webhook_url(settings),
					"webhookVersion": WEBHOOK_VERSION,
					"webhookTypes": ["channel-hangup"],
				},
			},
			# API4Com takes the raw token, without "Bearer"
			headers={"Authorization": settings.get_password("api_token")},
			timeout=20,
		)
	except requests.RequestException:
		frappe.log_error(title="API4Com: webhook registration failed")
		frappe.throw(_("Could not reach API4Com. Please try again in a few minutes."))
	if response.status_code in (401, 403):
		frappe.throw(_("API4Com refused the token. Check that it was copied whole and has not expired."))
	if response.status_code >= 400:
		frappe.log_error(
			title="API4Com: webhook registration refused",
			message=f"HTTP {response.status_code}: {response.text[:500]}",
		)
		frappe.throw(_("API4Com refused the webhook registration (HTTP {0}).").format(response.status_code))


@frappe.whitelist()
def set_extension(user: str, extension: str | None = None) -> dict:
	"""Kept for screens opened before the per-operator extensions (credtech#268)."""
	from crm.integrations.voip.api import set_extension as set_operator_extension

	return set_operator_extension("api4com", user, extension)
