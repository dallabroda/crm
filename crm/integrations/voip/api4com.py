"""API4Com: their `channel-hangup` webhook (v1.4) in the common call format of `record_call`.

Reference: https://developers.api4com.com/integration-own-webphone.html
What the doc doesn't say (incoming calls, time zone, causes) is confirmed in credtech#100.
"""

import re

from frappe.utils import cint, get_datetime

# Hangup causes (FreeSWITCH/Q.850 names) of a call that rang but nobody picked up
NO_ANSWER_CAUSES = {
	"NO_ANSWER",
	"NO_USER_RESPONSE",
	"ORIGINATOR_CANCEL",
	"NORMAL_CLEARING",
	"ALLOTTED_TIMEOUT",
}


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
