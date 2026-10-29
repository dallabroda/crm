"""Nvoip adapter (credtech#269): no call webhook, so every call is read by polling.

Reference: https://nvoip.docs.apiary.io/ (Apiary blueprint, v2). The doc is thin in two places
this adapter works around:

1. `POST /calls/` (click-to-call) takes no custom field, so it can't echo the deal back like
   API4Com's `metadata`. The deal (and the extension/number, needed to build the common call
   format later) is kept in `CRM Nvoip Pending Call`, keyed by the `callId` Nvoip returns, until
   the poller reads the call's outcome.
2. `GET /calls/history` rows have no id at all. One is made up from the row's own fields
   (date, direction, both numbers, duration): stable across repeated polls of the same call,
   but if Nvoip ever changes a row after the fact (a recording link appearing later, say) it
   would be read as a new call rather than an update to the old one. Confirm with a real account
   before depending on it, same as credtech#100 for API4Com.

Only inbound calls go through the history endpoint: outbound ones are already covered by the
pending-call tracking above, and including them here too would record every call twice.
"""

import hashlib
import re
from datetime import timedelta

import frappe
import requests
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from crm.integrations.voip.base import Operator

API_URL = "https://api.nvoip.com.br/v2"
# the fixed client credential Nvoip's own doc uses to request a token; not specific to any
# company's account (that's the username/password in the token request body)
BASIC_AUTH = "Basic TnZvaXBBcGlWMjpUblp2YVhCQmNHbFdNakl3TWpFPQ=="
TOKEN_CACHE_KEY = "crm_nvoip_access_token"

# GET /calls state values, per their doc
TALKING_STATES = {"calling_origin", "calling_destination", "established"}
CALL_STATUS = {"finished": "Completed", "noanswer": "No Answer", "busy": "Busy", "failed": "Failed"}
# a pending call stuck without a terminal state (Nvoip error, deleted call) is abandoned after this
GIVE_UP_AFTER = timedelta(days=1)


class Nvoip(Operator):
	key = "nvoip"
	medium = "Nvoip"
	settings_doctype = "CRM Nvoip Settings"
	# the doc's only concrete example is a 4-digit sub-account id; the real limit isn't stated
	extension_pattern = r"\d{1,20}"

	def list_calls(self, settings, since) -> list[dict]:
		return poll_pending_calls(settings) + poll_inbound_history(settings)

	def originate_call(self, settings, extension: str, number: str, deal: str | None) -> str | None:
		return originate_call(settings, extension, number, deal)


def originate_call(settings, extension: str, number: str, deal: str | None) -> str | None:
	"""POST /calls/: `caller` is the salesperson's own Nvoip extension, `called` the destination
	in plain national digits (their doc's only example has none of +55/E.164)."""
	response = _request(
		settings, "post", "/calls/", json={"caller": extension, "called": to_national(number)}
	)
	if response.status_code >= 400:
		frappe.throw(call_error(response.status_code))
	try:
		call_id = str(response.json().get("callId") or "") or None
	except ValueError:
		call_id = None
	if call_id:
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": call_id,
				"deal": deal,
				"extension": extension,
				"number": number,
			}
		).insert(ignore_permissions=True)
	return call_id


def call_error(status: int) -> str:
	if status == 401:
		return _("Nvoip refused the numbersip or user-token. Check them in the telephony settings.")
	if status == 429:
		return _("Too many calls in a minute. Wait a moment and try again.")
	return _("Nvoip refused the call (HTTP {0}).").format(status)


def poll_pending_calls(settings) -> list[dict]:
	"""GET /calls?callId=... for every click-to-call still waiting: still talking is read again
	next run, a terminal state is recorded and the wait is over either way.

	The pending row is deleted only once `CRM Call Log` already has the call — never in the same
	pass that first returns it for recording. `poll()` commits as soon as the first call in this
	batch records successfully, which would otherwise also commit every pending row deleted here
	so far, even ones whose own `record_call` hasn't run yet; if that one then raised, its row
	was already gone and the call could never be read again (credtech#269, review of crm#71)."""
	calls = []
	for call_id in frappe.get_all("CRM Nvoip Pending Call", pluck="name"):
		if frappe.db.exists("CRM Call Log", call_id):
			# recorded by a previous run: safe to stop tracking it now, with no API call needed
			frappe.delete_doc("CRM Nvoip Pending Call", call_id, ignore_permissions=True)
			continue

		row = frappe.get_doc("CRM Nvoip Pending Call", call_id)
		response = _request(settings, "get", "/calls", params={"callId": call_id})
		if response.status_code >= 400:
			if now_datetime() - get_datetime(row.creation) > GIVE_UP_AFTER:
				frappe.delete_doc("CRM Nvoip Pending Call", call_id, ignore_permissions=True)
			continue

		data = response.json()
		state = data.get("state")
		if state in TALKING_STATES:
			continue

		calls.append(
			{
				"id": call_id,
				"type": "Outgoing",
				"extension": row.extension,
				"number": row.number,
				"status": CALL_STATUS.get(state, "Failed"),
				"start_time": None,
				"end_time": None,
				"duration": cint(data.get("talkingDurationSeconds") or 0),
				"recording_url": data.get("linkAudio") or None,
				"deal": row.deal,
			}
		)
	return calls


def poll_inbound_history(settings) -> list[dict]:
	"""GET /calls/history: only `type=inbound`, read for today and yesterday every time (their
	`date` param has no finer resolution), so a call near midnight is never missed."""
	calls = []
	for date in ("today", "yesterday"):
		response = _request(settings, "get", "/calls/history", params={"type": "inbound", "date": date})
		if response.status_code >= 400:
			frappe.log_error(title="Nvoip: could not read the call history")
			continue
		for row in history_rows(response):
			calls.append(parse_history_row(row))
	return calls


def history_rows(response) -> list[dict]:
	# the doc shows one row's shape, not how a list of them is wrapped; read generously
	try:
		body = response.json()
	except ValueError:
		return []
	if isinstance(body, list):
		return body
	if isinstance(body, dict):
		return body.get("data") or body.get("calls") or ([body] if body.get("date") else [])
	return []


def parse_history_row(row: dict) -> dict:
	started = parse_history_date(row.get("date"))
	duration = hms_to_seconds(row.get("duration"))
	return {
		"id": history_row_id(row),
		"type": "Incoming",
		"extension": None,
		"number": row.get("origin"),
		# only "Completada" is confirmed by the doc; anything else is read as failed until a real
		# account shows the other values
		"status": "Completed" if row.get("status") == "Completada" else "Failed",
		"start_time": started,
		"end_time": (started + timedelta(seconds=duration)) if started else None,
		"duration": duration,
		"recording_url": row.get("audio") or None,
		"deal": None,
	}


def history_row_id(row: dict) -> str:
	"""Nvoip's history rows carry no id; one is made up from the row itself (module docstring)."""
	basis = "|".join(
		str(row.get(field) or "") for field in ("date", "type", "origin", "destination", "duration")
	)
	return "nvoip-" + hashlib.sha1(basis.encode()).hexdigest()[:24]


def parse_history_date(value: str | None):
	try:
		return get_datetime(value) if value else None
	except Exception:
		return None


def hms_to_seconds(value: str | None) -> int:
	try:
		hours, minutes, seconds = (int(part) for part in (value or "0:0:0").split(":"))
		return hours * 3600 + minutes * 60 + seconds
	except (ValueError, AttributeError):
		return 0


def to_national(number: str) -> str:
	"""Plain national digits: Nvoip's doc only shows DDD + number, no +55/E.164."""
	digits = re.sub(r"\D", "", number or "")
	if digits.startswith("55") and len(digits) > 11:
		digits = digits[2:]
	return digits


def _request(settings, method: str, path: str, **kwargs):
	token = _access_token(settings)
	response = requests.request(
		method, f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=20, **kwargs
	)
	if response.status_code == 401:
		# the cached token was revoked or expired early: one fresh attempt with a new one
		frappe.cache().delete_value(TOKEN_CACHE_KEY)
		token = _access_token(settings)
		response = requests.request(
			method, f"{API_URL}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=20, **kwargs
		)
	return response


def _access_token(settings) -> str:
	cached = frappe.cache().get_value(TOKEN_CACHE_KEY)
	if cached and get_datetime(cached["expires_at"]) > now_datetime():
		return cached["access_token"]
	return _password_grant(settings)


def _password_grant(settings) -> str:
	try:
		response = requests.post(
			f"{API_URL}/oauth/token",
			data={
				"username": settings.numbersip,
				"password": settings.get_password("user_token"),
				"grant_type": "password",
			},
			headers={"Authorization": BASIC_AUTH, "Content-Type": "application/x-www-form-urlencoded"},
			timeout=20,
		)
	except requests.RequestException:
		frappe.log_error(title="Nvoip: could not reach the token endpoint")
		frappe.throw(_("Could not reach Nvoip. Please try again in a few minutes."))
	if response.status_code >= 400:
		frappe.throw(_("Nvoip refused the numbersip or user-token. Check them in the telephony settings."))
	token = response.json()
	expires_at = frappe.utils.add_to_date(now_datetime(), seconds=max(cint(token.get("expires_in")) - 60, 0))
	frappe.cache().set_value(
		TOKEN_CACHE_KEY, {"access_token": token["access_token"], "expires_at": str(expires_at)}
	)
	return token["access_token"]
