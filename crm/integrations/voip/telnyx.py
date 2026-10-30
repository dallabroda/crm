"""Telnyx adapter (credtech#270): click-to-call through Call Control, calls recorded from its webhooks.

Reference: https://developers.telnyx.com/docs/voice/call-control (API v2) and the Call Control OpenAPI
spec (`call-control.json`). The customer hires Telnyx and creates a Call Control Application; the CRM
only places calls through it, so the customer's own numbers keep their inbound routing.

A click-to-call is two legs:

1. `POST /calls` rings the salesperson (their phone in +E.164 or a SIP address, the "extension");
2. when they answer (`call.answered`), `POST /calls/{id}/actions/transfer` rings the customer and bridges
   the two, recording from the customer's answer.

Every webhook of the call comes to this CRM (`webhook_url` on both commands) carrying `client_state`, the
base64 JSON the CRM sent: the CRM's own call id, the deal, the numbers and which leg it is. The customer's
leg hanging up records the call; the salesperson's leg only does when they never answered (nothing else
will). `call.recording.saved` then adds the recording. Its links expire in minutes, so the call log keeps
the recording's API address and the recording proxy asks Telnyx for a fresh link each time it plays.

Telnyx signs every webhook with Ed25519 (`telnyx-signature-ed25519` over `{telnyx-timestamp}|{body}`,
checked with the account's public key); the secret in the URL is checked as well.

Not run against a real account yet: the test account is the owner's, at the end of credtech#270.
"""

import base64
import binascii
import json
import re
import time
from datetime import datetime, timezone

import frappe
import requests
from frappe import _
from frappe.utils import cint
from frappe.utils.data import convert_utc_to_system_timezone

from crm.integrations.voip.base import Operator

API_URL = "https://api.telnyx.com/v2"
WEBHOOK_PATH = "/api/method/crm.integrations.voip.webhook.telnyx"
# How long each leg rings before giving up, in seconds (Telnyx: 5 to 600, default 30)
RING_SECONDS = 30
# A signed webhook older than this is refused (replays); the Telnyx SDKs use the same 5 minutes
SIGNATURE_TOLERANCE = 300
# Recording found by `call.recording.saved` before the hangup recorded the call: kept here for a day
RECORDING_CACHE_KEY = "crm_telnyx_recording:{}"

# call.hangup `hangup_cause` (call-control.json) to CRM Call Log status
CALL_STATUS = {
	"normal_clearing": "Completed",
	"time_limit": "Completed",
	"no_answer": "No Answer",
	"timeout": "No Answer",
	"user_busy": "Busy",
	"originator_cancel": "Canceled",
	"call_rejected": "Failed",
	"not_found": "Failed",
	"unspecified": "Failed",
}
# The salesperson's leg ending like this means they never answered, so the customer was never called
UNANSWERED_CAUSES = {"no_answer", "timeout", "user_busy", "call_rejected", "not_found", "originator_cancel"}

E164 = re.compile(r"\+[1-9]\d{7,14}")
SIP_ADDRESS = re.compile(r"sip:[^@\s]+@[^@\s]+")


class Telnyx(Operator):
	key = "telnyx"
	medium = "Telnyx"
	settings_doctype = "CRM Telnyx Settings"

	def validate_extension(self, extension: str):
		"""The line Telnyx rings first: the salesperson's phone or SIP address, not a short extension."""
		if not (E164.fullmatch(extension or "") or SIP_ADDRESS.fullmatch(extension or "")):
			frappe.throw(
				_(
					"Use the salesperson's phone in international format (+5548999990000) or a SIP address (sip:name@domain)."
				)
			)

	def is_call_event(self, payload: dict) -> bool:
		return call_to_record(payload) is not None

	def parse_webhook(self, payload: dict) -> dict:
		return call_to_record(payload)

	def originate_call(self, settings, extension: str, number: str, deal: str | None) -> str | None:
		return originate_call(settings, extension, number, deal)

	def recording_location(self, settings, recording_url: str) -> str:
		return fresh_recording_link(settings, recording_url)


# Click-to-call


def originate_call(settings, extension: str, number: str, deal: str | None) -> str:
	"""Rings the salesperson first (leg A); the customer is called when they answer (`on_answered`)."""
	call_id = "telnyx-" + frappe.generate_hash(length=24)
	state = {"id": call_id, "leg": "agent", "deal": deal, "extension": extension, "number": to_e164(number)}
	response = _request(
		settings,
		"post",
		"/calls",
		json={
			"connection_id": settings.connection_id,
			"to": extension,
			"from": settings.caller_number,
			"client_state": encode_state(state),
			"webhook_url": webhook_url(settings),
			"timeout_secs": RING_SECONDS,
			"command_id": call_id,
		},
	)
	if response.status_code >= 400:
		frappe.log_error(
			title="Telnyx: click-to-call refused",
			message=f"HTTP {response.status_code}: {response.text[:500]}",
		)
		frappe.throw(call_error(response.status_code))
	return call_id


def on_answered(settings, payload: dict):
	"""The salesperson answered: transfer the call to the customer, recording from their answer."""
	data = payload.get("data") or {}
	call = data.get("payload") or {}
	state = decode_state(call.get("client_state"))
	if data.get("event_type") != "call.answered" or not state or state.get("leg") != "agent":
		return
	customer = {**state, "leg": "customer"}
	response = _request(
		settings,
		"post",
		f"/calls/{call['call_control_id']}/actions/transfer",
		json={
			"to": state["number"],
			"from": settings.caller_number,
			"target_leg_client_state": encode_state(customer),
			"webhook_url": webhook_url(settings),
			"timeout_secs": RING_SECONDS,
			"record": "record-from-answer",
			"record_format": "mp3",
			"command_id": state["id"] + "-transfer",
		},
	)
	if response.status_code >= 400:
		frappe.log_error(
			title="Telnyx: could not call the customer",
			message=f"HTTP {response.status_code}: {response.text[:500]}",
		)
		record_failed_transfer(settings, call, state)


def record_failed_transfer(settings, call: dict, state: dict):
	"""Telnyx refused to call the customer: the salesperson is not left on a silent line, and the attempt
	stays on the deal as a failed call (no customer leg will ever send a hangup)."""
	from crm.integrations.voip.webhook import record_call

	_request(settings, "post", f"/calls/{call['call_control_id']}/actions/hangup", json={})
	started = to_system_time(call.get("start_time"))
	record_call(
		{
			"id": state["id"],
			"type": "Outgoing",
			"extension": state.get("extension"),
			"number": state.get("number"),
			"status": "Failed",
			"start_time": started,
			"end_time": started,
			"duration": 0,
			"recording_url": None,
			"deal": state.get("deal"),
		},
		"Telnyx",
	)


def call_error(status: int) -> str:
	if status == 401:
		return _("Telnyx refused the API key. Check it in the telephony settings.")
	if status == 403:
		return _("Your Telnyx account does not allow this call (balance, verification or outbound profile).")
	if status == 404:
		return _("The Telnyx Call Control Application was not found. Check its ID in the telephony settings.")
	if status == 422:
		return _(
			"Telnyx did not accept the numbers of this call. Check your extension and the caller number."
		)
	if status == 429:
		return _("Too many calls in a minute. Wait a moment and try again.")
	return _("Telnyx refused the call (HTTP {0}).").format(status)


# Webhooks


def call_to_record(payload: dict) -> dict | None:
	"""The call in the common format for a `call.hangup` that ends a click-to-call; None for any other event."""
	data = payload.get("data") or {}
	if data.get("event_type") != "call.hangup":
		return None
	call = data.get("payload") or {}
	state = decode_state(call.get("client_state"))
	if not state or not state.get("id"):
		return None
	cause = call.get("hangup_cause")
	# the customer's leg records the call; the salesperson's only when they never answered, and then the
	# customer was never called
	agent_leg = state.get("leg") == "agent"
	if agent_leg and cause not in UNANSWERED_CAUSES:
		return None

	start = to_system_time(call.get("start_time"))
	end = to_system_time(data.get("occurred_at"))
	return {
		"id": state["id"],
		"type": "Outgoing",
		"extension": state.get("extension"),
		"number": state.get("number"),
		"status": "Canceled" if agent_leg else CALL_STATUS.get(cause, "Failed"),
		"start_time": start,
		"end_time": end,
		# Telnyx gives no talk time: from the leg's start (ringing included) to its hangup
		"duration": max(int((end - start).total_seconds()), 0) if start and end else 0,
		"recording_url": frappe.cache().get_value(RECORDING_CACHE_KEY.format(state["id"])),
		"deal": state.get("deal"),
	}


def on_recording_saved(settings, payload: dict):
	"""Keeps the recording's API address on the call log (or until the hangup records it)."""
	data = payload.get("data") or {}
	call = data.get("payload") or {}
	state = decode_state(call.get("client_state"))
	if data.get("event_type") != "call.recording.saved" or not state or not state.get("id"):
		return
	recording_id = find_recording(settings, call.get("call_session_id"))
	if not recording_id:
		return
	address = f"{API_URL}/recordings/{recording_id}"
	# the same lock record_call holds, so the hangup can't be saving the call log at this moment
	lock = f"crm_voip:Telnyx:{state['id']}"[:64]
	if not frappe.db.sql("SELECT GET_LOCK(%s, 30)", lock)[0][0]:
		frappe.throw(_("Call {0} is being recorded").format(state["id"]))
	try:
		if frappe.db.exists("CRM Call Log", state["id"]):
			frappe.db.set_value("CRM Call Log", state["id"], "recording_url", address)
		else:
			frappe.cache().set_value(RECORDING_CACHE_KEY.format(state["id"]), address, expires_in_sec=86400)
		frappe.db.commit()
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", lock)


def attach_waiting_recording(payload: dict):
	"""After a hangup is recorded: a recording that arrived while it was being parsed is attached now."""
	data = payload.get("data") or {}
	state = decode_state((data.get("payload") or {}).get("client_state"))
	if data.get("event_type") != "call.hangup" or not state or not state.get("id"):
		return
	key = RECORDING_CACHE_KEY.format(state["id"])
	address = frappe.cache().get_value(key)
	if not address or not frappe.db.exists("CRM Call Log", state["id"]):
		return
	if not frappe.db.get_value("CRM Call Log", state["id"], "recording_url"):
		frappe.db.set_value("CRM Call Log", state["id"], "recording_url", address)
		frappe.db.commit()
	frappe.cache().delete_value(key)


def find_recording(settings, call_session_id: str | None) -> str | None:
	if not call_session_id:
		return None
	response = _request(settings, "get", "/recordings", params={"filter[call_session_id]": call_session_id})
	if response.status_code >= 400:
		frappe.log_error(title="Telnyx: could not find the recording", message=f"HTTP {response.status_code}")
		return None
	recordings = response.json().get("data") or []
	return recordings[0].get("id") if recordings else None


def fresh_recording_link(settings, recording_url: str) -> str:
	"""A stored recording address becomes a download link valid for a few minutes."""
	if not recording_url.startswith(f"{API_URL}/recordings/"):
		return recording_url
	response = _request(settings, "get", recording_url[len(API_URL) :])
	if response.status_code >= 400:
		frappe.throw(_("Telnyx did not return the recording (HTTP {0}).").format(response.status_code))
	urls = (response.json().get("data") or {}).get("download_urls") or {}
	link = urls.get("mp3") or urls.get("wav")
	if not link:
		frappe.throw(_("Telnyx did not return the recording."))
	return link


def verify_signature(settings, headers, body: bytes):
	"""Ed25519 signature of `{timestamp}|{body}` with the account's public key, at most 5 minutes old."""
	from cryptography.exceptions import InvalidSignature
	from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

	signature = headers.get("telnyx-signature-ed25519")
	timestamp = headers.get("telnyx-timestamp")
	if (
		not settings.public_key
		or not signature
		or not timestamp
		or abs(time.time() - cint(timestamp)) > SIGNATURE_TOLERANCE
	):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	try:
		key = Ed25519PublicKey.from_public_bytes(base64.b64decode(settings.public_key))
		key.verify(base64.b64decode(signature), timestamp.encode() + b"|" + body)
	except (InvalidSignature, ValueError, TypeError, binascii.Error):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


# Helpers


def webhook_url(settings) -> str:
	return frappe.utils.get_url(f"{WEBHOOK_PATH}?key={settings.get_password('webhook_secret')}")


def encode_state(state: dict) -> str:
	return base64.b64encode(json.dumps(state, separators=(",", ":")).encode()).decode()


def decode_state(value: str | None) -> dict | None:
	"""The CRM's own client_state; anything else (a call the CRM didn't place) is None."""
	if not value:
		return None
	try:
		state = json.loads(base64.b64decode(value))
	except (ValueError, binascii.Error):
		return None
	return state if isinstance(state, dict) and str(state.get("id", "")).startswith("telnyx-") else None


def to_e164(number: str) -> str:
	"""Telnyx dials +E.164. A Brazilian number without the country code (DDD + number) gets +55."""
	digits = re.sub(r"\D", "", number or "")
	if (number or "").strip().startswith("+"):
		return "+" + digits
	if len(digits) in (10, 11):
		return "+55" + digits
	return "+" + digits


def to_system_time(value: str | None):
	"""Telnyx sends UTC ISO 8601 ("2018-02-02T22:20:27.521992Z"); the call log keeps system time."""
	if not value:
		return None
	try:
		moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
	except ValueError:
		return None
	if moment.tzinfo:
		moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
	return convert_utc_to_system_timezone(moment).replace(tzinfo=None)


def _request(settings, method: str, path: str, **kwargs):
	try:
		return requests.request(
			method,
			f"{API_URL}{path}",
			headers={"Authorization": f"Bearer {settings.get_password('api_key')}"},
			timeout=20,
			**kwargs,
		)
	except requests.RequestException:
		frappe.log_error(title="Telnyx: could not reach the API")
		frappe.throw(_("Could not reach Telnyx. Please try again in a few minutes."))
