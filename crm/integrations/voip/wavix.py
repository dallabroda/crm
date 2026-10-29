"""Wavix: their `post-call` webhook (the only event with the call's final duration and
disposition) in the common call format of `record_call` (credtech#271).

Reference: https://wavix.github.io/wavix-openapi/wavix-api.yaml (`CallStatusWebhook`).

Click-to-call is not implemented yet. Wavix's REST `POST /v1/calls` places a single PSTN leg
(from one of the company's own Wavix numbers to a destination) with an AMD/voicemail-detection
option — a shape built for campaigns, not a live agent call. Wavix's actual agent-facing product
is the "Wavix Embeddable" browser widget (a SIP/WebRTC softphone the agent's browser registers
as), for which the REST spec only has a token endpoint (`POST /v2/webrtc/tokens`); the widget's
own JS SDK (its `dial()`/event API) isn't in the OpenAPI or AsyncAPI specs and can't be verified
without a sandbox account — needs confirming before it's built, same spirit as Baldussi
(credtech#193). Calls made another way (the Wavix panel, a direct SIP call) still land on the
timeline through this webhook, by phone number.
"""

from datetime import timedelta
from zoneinfo import ZoneInfo

import frappe
import requests
from frappe.utils import cint, get_datetime

from crm.integrations.voip.base import Operator

API_URL = "https://api.wavix.com/v1"

CALL_STATUS = {"answered": "Completed", "noanswer": "No Answer", "busy": "Busy", "failed": "Failed"}


class Wavix(Operator):
	key = "wavix"
	medium = "Wavix"
	settings_doctype = "CRM Wavix Settings"

	def is_call_event(self, payload: dict) -> bool:
		# the post-call payload has no event type of its own; "disposition" is what sets it apart
		# from the on-call one (never registered: credtech#271 only asks for the post-call webhook)
		return bool(payload.get("disposition")) and bool(payload.get("uuid"))

	def parse_webhook(self, payload: dict) -> dict:
		return parse_post_call(payload)

	def recording_auth(self, settings):
		# the URL stored in recording_url is the one GET /v1/recordings/{call_id} already resolved
		# (with our own bearer token) when the webhook was received; nothing further to add here
		return None


def parse_post_call(payload: dict) -> dict:
	outgoing = payload.get("direction") == "outbound"
	started = to_datetime(payload.get("date"))
	duration = cint(payload.get("duration") or 0)
	return {
		"id": str(payload["uuid"]),
		"type": "Outgoing" if outgoing else "Incoming",
		# Wavix's post-call payload has no concept of which agent took the call
		"extension": None,
		"number": payload.get("to") if outgoing else payload.get("from"),
		"status": CALL_STATUS.get(payload.get("disposition"), "Failed"),
		"start_time": started,
		"end_time": started + timedelta(seconds=duration) if started else None,
		"duration": duration,
		"recording_url": resolve_recording_url(payload["uuid"]),
		# no click-to-call yet, so no deal id to send with the call (module docstring)
		"deal": None,
	}


def resolve_recording_url(call_id: str) -> str | None:
	"""GET /v1/recordings/{call_id} redirects to the download URL (its own `Location` header);
	fetched now, with our token, instead of at playback time, since the proxy (`get_recording_url`)
	has no way to send a Wavix bearer token (unconfirmed with a real account: credtech#271)."""
	settings = frappe.get_single("CRM Wavix Settings")
	try:
		response = requests.get(
			f"{API_URL}/recordings/{call_id}",
			headers={"Authorization": f"Bearer {settings.get_password('api_key')}"},
			timeout=20,
			allow_redirects=False,
		)
	except requests.RequestException:
		frappe.log_error(title="Wavix: could not resolve the recording URL")
		return None
	if response.status_code == 400:
		return None  # the recording was already deleted
	if response.status_code >= 400:
		frappe.log_error(
			title="Wavix: could not resolve the recording URL", message=f"HTTP {response.status_code}"
		)
		return None
	return response.headers.get("Location") or None


def to_datetime(value):
	"""Wavix's dates carry a timezone (`Z`/`+00:00`); MariaDB's plain `datetime` column doesn't
	take that suffix, so it's converted to the system timezone and dropped, same as Twilio does."""
	try:
		parsed = get_datetime(value) if value else None
	except Exception:
		return None
	if parsed and parsed.tzinfo:
		parsed = parsed.astimezone(ZoneInfo(frappe.utils.get_system_timezone())).replace(tzinfo=None)
	return parsed
