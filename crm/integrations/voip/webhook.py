"""Call webhooks of the telephony operators: one route per operator, each with its adapter.

The customer hires the operator directly; at the end of each call the operator POSTs it here
and the call lands on the timeline of the deal(s) it belongs to (credtech#47).
"""

import hmac

import frappe
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline
from crm.integrations.api import get_contact_by_phone_number
from crm.integrations.voip import api4com as api4com_adapter

# <site>/api/method/crm.integrations.voip.webhook.api4com?key=<webhook secret of the company>


# API4Com doesn't sign its webhook: the secret in the URL is what authenticates it
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def api4com(**kwargs):
	settings = frappe.get_single("CRM API4Com Settings")
	authorize(frappe.request.args.get("key"), settings)

	payload = frappe.request.get_json(silent=True) or {}
	if payload.get("eventType") != "channel-hangup" or not payload.get("id"):
		return

	# only the body is logged: the query string carries the secret
	request_log = create_request_log(
		payload,
		request_description="API4Com Call",
		service_name="API4Com",
		request_headers=frappe.request.headers,
		is_remote_request=1,
	)
	frappe.db.commit()  # the log survives a failed recording's rollback
	try:
		record_call(api4com_adapter.parse_hangup(payload), "API4Com", settings.pipeline)
		request_log.status = "Completed"
	except Exception:
		frappe.db.rollback()
		request_log.status = "Failed"
		request_log.error = frappe.get_traceback()
		frappe.log_error(title="API4Com: error while recording a call")
	finally:
		request_log.save(ignore_permissions=True)
		frappe.db.commit()


def authorize(key: str | None, settings):
	secret = settings.get_password("webhook_secret", raise_exception=False) if settings.enabled else None
	if not secret or not key or not hmac.compare_digest(key.encode(), secret.encode()):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def record_call(call: dict, medium: str, pipeline: str | None):
	"""One call log per call id: a repeated delivery updates the same row and links nothing new.
	The lock is held until after the commit, so two deliveries of a call can't both create a deal."""
	lock = f"crm_voip:{medium}:{call['id']}"[:64]
	if not frappe.db.sql("SELECT GET_LOCK(%s, 30)", lock)[0][0]:
		frappe.throw(_("Call {0} is being recorded").format(call["id"]))
	try:
		is_new = not frappe.db.exists("CRM Call Log", call["id"])
		call_log = frappe.new_doc("CRM Call Log") if is_new else frappe.get_doc("CRM Call Log", call["id"])
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
		if is_new:
			link_to_deals(call_log, call, pipeline, agent)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", lock)


def agent_of_extension(extension: str, medium: str) -> str | None:
	if not extension or medium != "API4Com":
		return None
	return frappe.db.get_value("CRM Telephony Agent", {"api4com_extension": extension}, "user")


def link_to_deals(call_log, call: dict, pipeline: str | None, agent: str | None):
	"""The deal the click-to-call came from; else every open deal of the number (owner rule,
	credtech#99); else a new deal in the entry pipeline. The first deal is the call's reference,
	the others are links, so the call shows once on each timeline."""
	if call["deal"] and frappe.db.exists("CRM Deal", call["deal"]):
		deals = [call["deal"]]
	else:
		contact = get_contact_by_phone_number(call["number"]) if call["number"] else {}
		deals = contact.get("deals") or [create_deal_for_call(call["number"], contact, pipeline, agent)]
	deals = [deal for deal in deals if deal]
	if not deals:
		return
	call_log.reference_doctype = "CRM Deal"
	call_log.reference_docname = deals[0]
	for deal in deals[1:]:
		call_log.link_with_reference_doc("CRM Deal", deal)


def create_deal_for_call(number: str, contact: dict, pipeline: str | None, agent: str | None) -> str | None:
	"""Owner rule (credtech#47, #99): a number nobody has, or whose deals are all closed, opens a deal
	in the entry pipeline, the same way as the other automatic entries (credtech#70). The person who
	took or made the call owns it when they are in that pipeline; otherwise its distribution decides."""
	if not number:  # anonymous caller: nothing to open a deal for
		return None
	pipeline = pipeline or get_default_pipeline("Administrator")
	if not pipeline:
		frappe.throw(_("No pipeline to open a deal for the call"))
	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": contact.get("full_name") or number,
			# the number exactly as the contact has it, so the deal reuses that contact
			"mobile_no": contact.get("matched_phone") or number,
			"source": lead_source("API4Com"),
			"pipeline": pipeline,
			"lead_owner": agent,
		}
	).insert(ignore_permissions=True)
	return lead.flags.duplicate_of or frappe.db.get_value("CRM Deal", {"lead": lead.name})


def lead_source(name: str) -> str:
	if not frappe.db.exists("CRM Lead Source", name):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": name}).insert(ignore_permissions=True)
	return name
