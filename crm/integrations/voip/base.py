"""What every telephony operator adapter implements (credtech#268).

The customer hires the operator directly; the CRM only integrates. Each operator converts its own
call data into the common call format of `record_call`:

	{"id", "type": "Outgoing" | "Incoming", "extension", "number", "status", "start_time",
	 "end_time", "duration", "recording_url", "deal"}

An operator gets calls in by webhook (`parse_webhook`), by polling (`list_calls`) or both, and
places calls from the deal (`originate_call`) when its API allows it.
"""

import re

import frappe
from frappe import _


class Operator:
	# route of its webhook: crm.integrations.voip.webhook.<key>
	key: str = ""
	# name in the CRM: CRM Call Log.telephony_medium, CRM Telephony Agent.default_medium
	medium: str = ""
	# Single DocType with `enabled` and the credentials of the company
	settings_doctype: str = ""
	# what an extension (ramal) of this operator looks like
	extension_pattern: str = r"\d{1,6}"

	def is_enabled(self) -> bool:
		return bool(frappe.db.get_single_value(self.settings_doctype, "enabled"))

	def get_settings(self):
		return frappe.get_single(self.settings_doctype)

	def validate_extension(self, extension: str):
		"""An operator whose extensions look different overrides this and `extension_pattern`."""
		if not re.fullmatch(self.extension_pattern, extension or ""):
			frappe.throw(_("An extension has 1 to 6 digits."))

	# Webhook

	def is_call_event(self, payload: dict) -> bool:
		"""Whether this webhook body is a call to record; anything else is answered and dropped."""
		return False

	def parse_webhook(self, payload: dict) -> dict:
		raise NotImplementedError

	# Polling, for operators without a call webhook

	@property
	def polls(self) -> bool:
		return type(self).list_calls is not Operator.list_calls

	def list_calls(self, settings, since) -> list[dict]:
		"""Calls that started or changed since `since`, already in the common format."""
		raise NotImplementedError

	# Click-to-call

	@property
	def can_originate(self) -> bool:
		return type(self).originate_call is not Operator.originate_call

	def originate_call(self, settings, extension: str, number: str, deal: str | None) -> str | None:
		"""Ask the operator to call `number` from the salesperson's `extension`; `deal` must come
		back with the call so it lands on that deal. Returns the operator's call id, if it gives one."""
		raise NotImplementedError

	# Recordings

	def recording_auth(self, settings) -> tuple | None:
		"""(user, secret) the recording proxy sends to the operator; None for a plain link."""
		return None
