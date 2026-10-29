# Copyright (c) 2026, CredTech and contributors
# For license information, please see license.txt
"""Wavix settings of the company (credtech#271).

The customer hires Wavix directly and pastes the API key here; the CRM generates the webhook
secret and registers its own webhook at Wavix, so the customer copies no URL. Wavix's own
post-call webhook carries no signature or account id at all: the secret in the URL is the only
thing authenticating it (same situation as API4Com)."""

import frappe
import requests
from frappe import _
from frappe.model.document import Document

API_URL = "https://api.wavix.com/v1"
WEBHOOK_PATH = "/api/method/crm.integrations.voip.webhook.wavix"


class CRMWavixSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_key: DF.Password | None
		enabled: DF.Check
		webhook_secret: DF.Password | None
	# end: auto-generated types

	def validate(self):
		if not self.enabled:
			return
		if not self.get_password("api_key", raise_exception=False):
			frappe.throw(_("Paste the Wavix API key."))
		if self.api_key and not self.is_dummy_password(self.api_key):
			self.flags.register_webhook = True
		if not self.get_password("webhook_secret", raise_exception=False):
			self.webhook_secret = new_secret()
			self.flags.register_webhook = True

	def on_update(self):
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
	"""POST /v1/calls/webhooks (only `post-call`: the only event that carries the call's final
	duration and disposition, like API4Com's `channel-hangup`). Not yet run against the real API."""
	try:
		response = requests.post(
			f"{API_URL}/calls/webhooks",
			json={"url": webhook_url(settings), "event_type": "post-call"},
			headers={"Authorization": f"Bearer {settings.get_password('api_key')}"},
			timeout=20,
		)
	except requests.RequestException:
		frappe.log_error(title="Wavix: webhook registration failed")
		frappe.throw(_("Could not reach Wavix. Please try again in a few minutes."))
	if response.status_code in (401, 403):
		frappe.throw(_("Wavix refused the API key. Check that it was copied whole and has not expired."))
	if response.status_code >= 400:
		frappe.log_error(
			title="Wavix: webhook registration refused",
			message=f"HTTP {response.status_code}: {response.text[:500]}",
		)
		frappe.throw(_("Wavix refused the webhook registration (HTTP {0}).").format(response.status_code))
