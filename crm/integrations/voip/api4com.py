"""API4Com: their `channel-hangup` webhook (v1.4) in the common call format of `record_call`.

Reference: https://developers.api4com.com/integration-own-webphone.html
What the doc doesn't say (incoming calls, time zone, causes) is confirmed in credtech#100.
"""

import re

import frappe
import requests
from frappe import _
from frappe.utils import cint, get_datetime

from crm.integrations.voip.base import Operator

API_URL = "https://api.api4com.com/api/v1"
# Name of the integration created at API4Com for this CRM; the webhook only fires for calls with it
GATEWAY = "cred-hub"

# Hangup causes (FreeSWITCH/Q.850 names) of a call that rang but nobody picked up
NO_ANSWER_CAUSES = {
	"NO_ANSWER",
	"NO_USER_RESPONSE",
	"ORIGINATOR_CANCEL",
	"NORMAL_CLEARING",
	"ALLOTTED_TIMEOUT",
}


class API4Com(Operator):
	key = "api4com"
	medium = "API4Com"
	settings_doctype = "CRM API4Com Settings"

	def is_call_event(self, payload: dict) -> bool:
		return payload.get("eventType") == "channel-hangup" and bool(payload.get("id"))

	def parse_webhook(self, payload: dict) -> dict:
		return parse_hangup(payload)

	def originate_call(self, settings, extension: str, number: str, deal: str | None) -> str | None:
		"""POST /calls: API4Com rings the salesperson's webphone, then the customer. The deal goes in
		`metadata.entityId` and comes back in the `channel-hangup`. Not yet run against the real API
		(test account of credtech#100)."""
		metadata = {"gateway": GATEWAY}
		if deal:
			metadata["entityId"] = deal
		try:
			response = requests.post(
				f"{API_URL}/calls",
				json={"extension": extension, "caller": extension, "called": number, "metadata": metadata},
				# API4Com takes the raw token, without "Bearer"
				headers={"Authorization": settings.get_password("api_token")},
				timeout=90,
			)
		except requests.RequestException:
			# no retry: the call may already have been placed
			frappe.log_error(title="API4Com: click-to-call failed")
			frappe.throw(_("Could not reach API4Com. Please try again in a few minutes."))
		if response.status_code >= 400:
			frappe.log_error(
				title="API4Com: click-to-call refused",
				message=f"HTTP {response.status_code}: {response.text[:500]}",
			)
			frappe.throw(call_error(response.status_code, number))
		try:
			return str(response.json().get("id") or "") or None
		except ValueError:
			return None


def call_error(status: int, number: str) -> str:
	"""What the salesperson reads when API4Com refuses a click-to-call (codes from their doc)."""
	if status == 401:
		return _("API4Com refused the token. Check that it was copied whole and has not expired.")
	if status in (402, 403):
		return _("Your API4Com plan or account does not allow this call.")
	if status == 404:
		return _("Your extension was not found at API4Com. Check it in the telephony settings.")
	if status == 422:
		return _("API4Com did not accept the number {0}.").format(number)
	if status == 424:
		return _("Your API4Com webphone is offline. Open it and try again.")
	if status == 429:
		return _("Too many calls in a minute. Wait a moment and try again.")
	return _("API4Com refused the call (HTTP {0}).").format(status)


def parse_hangup(payload: dict) -> dict:
	extension, number = split_extension(str(payload.get("caller") or ""), str(payload.get("called") or ""))
	metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
	return {
		"id": str(payload["id"]),
		"type": "Outgoing" if payload.get("direction") == "outbound" else "Incoming",
		"extension": extension,
		"number": number,
		"status": call_status(payload),
		"start_time": to_datetime(payload.get("startedAt")),
		"end_time": to_datetime(payload.get("endedAt")),
		"duration": cint(payload.get("duration")),
		"recording_url": payload.get("recordUrl") or None,
		# the deal id the click-to-call sent in `metadata`, echoed back
		"deal": str(metadata.get("entityId") or "") or None,
	}


def split_extension(caller: str, called: str) -> tuple[str, str]:
	"""(extension, customer number). The doc names `caller` the extension; on an incoming call the
	customer may come as `caller` instead, so a short `called` next to a long `caller` is swapped."""
	if is_extension(called) and not is_extension(caller):
		return called, caller
	return caller, called


def is_extension(value: str) -> bool:
	return 0 < len(re.sub(r"\D", "", value)) <= 6


def call_status(payload: dict) -> str:
	if payload.get("answeredAt"):
		return "Completed"
	cause = str(payload.get("hangupCause") or "").upper()
	if cause == "USER_BUSY":
		return "Busy"
	if cause in NO_ANSWER_CAUSES:
		return "No Answer"
	return "Failed"


def to_datetime(value):
	try:
		return get_datetime(value) if value else None
	except Exception:
		return None
