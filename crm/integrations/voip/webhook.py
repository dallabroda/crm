"""Call webhooks of the telephony operators: one route per operator, each with its adapter.

The customer hires the operator directly; at the end of each call the operator POSTs it here
and the call lands on the timeline of the deal(s) it belongs to (credtech#47).
"""

import hmac
from decimal import Decimal

import frappe
from frappe import _
from frappe.integrations.utils import create_request_log
from frappe.utils import cstr, flt

from crm.integrations.api import get_contact_by_phone_number
from crm.integrations.voip.base import Operator
from crm.integrations.voip.operators import get_operator

# <site>/api/method/crm.integrations.voip.webhook.<operator>?key=<webhook secret of the company>
# One route per operator (credtech#47); each one only names its adapter.


# API4Com doesn't sign its webhook: the secret in the URL is what authenticates it
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def api4com(**kwargs):
	receive(get_operator("api4com"))


# Wavix's post-call webhook carries no signature or account id of its own either
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def wavix(**kwargs):
	receive(get_operator("wavix"))


# Telnyx signs its webhooks (Ed25519) on top of the secret in the URL. Besides the hangup that records the
# call, the salesperson answering moves the call on to the customer and a saved recording is attached.
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def telnyx(**kwargs):
	from crm.integrations.voip import telnyx as adapter

	operator = get_operator("telnyx")
	settings = operator.get_settings()
	authorize(frappe.request.args.get("key"), settings)
	adapter.verify_signature(settings, frappe.request.headers, frappe.request.get_data())
	payload = frappe.request.get_json(silent=True) or {}
	adapter.on_answered(settings, payload)
	adapter.on_recording_saved(settings, payload)
	receive(operator)
	adapter.attach_waiting_recording(payload)


# Zenvia doesn't sign its webhooks: the secret in the URL authenticates them. The company pastes two
# addresses in the Zenvia panel: "Chamada - Fim" and "DID - Fim de Chamada" (with tipo=did).
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def zenvia(**kwargs):
	receive(get_operator("zenvia"))


def receive(operator: Operator):
	authorize(frappe.request.args.get("key"), operator.get_settings())

	payload = frappe.request.get_json(silent=True) or {}
	if not operator.is_call_event(payload):
		return

	# only the body is logged: the query string carries the secret
	request_log = create_request_log(
		payload,
		request_description=f"{operator.medium} Call",
		service_name=operator.medium,
		request_headers=frappe.request.headers,
		is_remote_request=1,
	)
	frappe.db.commit()  # the log survives a failed recording's rollback
	try:
		record_call(operator.parse_webhook(payload), operator.medium)
		request_log.status = "Completed"
	except Exception:
		frappe.db.rollback()
		request_log.status = "Failed"
		request_log.error = frappe.get_traceback()
		frappe.log_error(title=f"{operator.medium}: error while recording a call")
	finally:
		request_log.save(ignore_permissions=True)
		frappe.db.commit()


def authorize(key: str | None, settings):
	secret = settings.get_password("webhook_secret", raise_exception=False) if settings.enabled else None
	if not secret or not key or not hmac.compare_digest(key.encode(), secret.encode()):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def record_call(call: dict, medium: str):
	"""One call log per call id: a repeated delivery updates the same row and links nothing new.
	The lock is held until after the commit, so two deliveries of a call can't both create the row."""
	lock = f"crm_voip:{medium}:{call['id']}"[:64]
	if not frappe.db.sql("SELECT GET_LOCK(%s, 30)", lock)[0][0]:
		frappe.throw(_("Call {0} is being recorded").format(call["id"]))
	try:
		is_new = not frappe.db.exists("CRM Call Log", call["id"])
		call_log = frappe.new_doc("CRM Call Log") if is_new else frappe.get_doc("CRM Call Log", call["id"])
		before = None if is_new else {field: comparable(call_log.get(field)) for field in RECORDED_FIELDS}
		outgoing = call["type"] == "Outgoing"
		call_log.update(
			{
				"id": call["id"],
				"type": call["type"],
				# both are mandatory: "-" when the operator leaves one out (anonymous caller, no extension)
				"from": (call["extension"] if outgoing else call["number"]) or "-",
				"to": (call["number"] if outgoing else call["extension"]) or "-",
				"status": call["status"],
				"start_time": call["start_time"],
				"end_time": call["end_time"],
				"duration": call["duration"],
				"recording_url": call["recording_url"],
				"telephony_medium": medium,
				"medium": medium,
			}
		)
		agent = agent_of_extension(call["extension"], medium)
		if agent:
			call_log.set("caller" if outgoing else "receiver", agent)
		# Polling reads recent calls again on every run: the same call with nothing new writes nothing
		# (no new "modified", no hooks)
		if before is not None and before == {
			field: comparable(call_log.get(field)) for field in RECORDED_FIELDS
		}:
			return
		if is_new:
			link_to_deals(call_log, call)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", lock)


RECORDED_FIELDS = (
	"type",
	"from",
	"to",
	"status",
	"start_time",
	"end_time",
	"duration",
	"recording_url",
	"telephony_medium",
	"medium",
	"caller",
	"receiver",
)


def comparable(value):
	"""Same value whether it came from the operator or back from the database (17 and 17.0, datetimes)."""
	if isinstance(value, bool | int | float | Decimal):
		return flt(value)
	return cstr(value)


def agent_of_extension(extension: str, medium: str) -> str | None:
	"""The user with this extension at the operator (CRM Telephony Agent is named by user)."""
	if not extension:
		return None
	return frappe.db.get_value(
		"CRM Telephony Extension",
		{"parenttype": "CRM Telephony Agent", "medium": medium, "extension": extension},
		"parent",
	)


def link_to_deals(call_log, call: dict):
	"""The deal the click-to-call came from; else every open deal of the number (credtech#99). The first
	deal is the call's reference, the others are links, so the call shows once on each timeline.
	Owner rule (credtech#47, 26/10/2026): a call never opens a deal. A number without an open deal only
	stays in the call history, linked to its contact when there is one."""
	if call["deal"] and frappe.db.exists("CRM Deal", call["deal"]):
		deals = [call["deal"]]
	else:
		contact = get_contact_by_phone_number(call["number"]) if call["number"] else {}
		deals = contact.get("deals") or []
		if not deals:
			if contact.get("name"):
				call_log.link_with_reference_doc("Contact", contact["name"])
			return
	call_log.reference_doctype = "CRM Deal"
	call_log.reference_docname = deals[0]
	for deal in deals[1:]:
		call_log.link_with_reference_doc("CRM Deal", deal)
