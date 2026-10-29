import json

import frappe
from frappe import _
from twilio.twiml.voice_response import VoiceResponse
from werkzeug.wrappers import Response

from crm.integrations.api import link_call_log_to_number

from .twilio_handler import IncomingCall, Twilio, TwilioCallDetails


def validate_twilio_request(args, require_application_sid: bool = False):
	twilio = Twilio.connect()
	if not twilio:
		frappe.throw(_("Twilio configuration is missing"), frappe.PermissionError)

	account_sid = frappe.utils.cstr(args.get("AccountSid"))
	if not account_sid or account_sid != frappe.utils.cstr(twilio.account_sid):
		frappe.throw(_("Invalid Twilio account"), frappe.PermissionError)

	if require_application_sid:
		application_sid = frappe.utils.cstr(args.get("ApplicationSid"))
		if not application_sid or application_sid != frappe.utils.cstr(twilio.application_sid):
			frappe.throw(_("Invalid Twilio application"), frappe.PermissionError)

	return twilio


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Twilio Settings", "enabled")


@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK."""
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller",
		}

	token = twilio.generate_voice_access_token(identity=frappe.session.user)
	return {"token": frappe.safe_decode(token)}


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server."""
	args = frappe._dict(kwargs)
	twilio = validate_twilio_request(args, require_application_sid=True)

	# the salesperson who placed the call, from the browser SDK's own identity (credtech#274)
	user = Twilio.emailid_from_identity(args.Caller.replace("client:", "").strip())

	# Generate TwiML instructions to make a call
	from_number = frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")
	if not from_number:
		resp = VoiceResponse()
		resp.say(_("Your account is not configured with a phone number. Please contact your administrator."))
		return Response(resp.to_xml(), mimetype="text/xml")

	call_details = TwilioCallDetails(args, call_from=from_number)
	try:
		# the deal id sent by the browser at click-to-call time (credtech#274), only if the caller
		# can read it (a browser could send any id): the phone number is otherwise the fallback,
		# same as an invalid one (credtech#47)
		create_call_log(call_details, deal=_readable_deal(args.get("DealId"), user))
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = twilio.generate_twilio_dial_response(from_number, args.To)
	return Response(resp.to_xml(), mimetype="text/xml")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	call_details = TwilioCallDetails(args)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype="text/xml")


def _readable_deal(deal: str | None, user: str) -> str | None:
	"""`deal`, only if `user` may read it. A browser sends `DealId` on its own say, so this is what
	actually enforces credtech#47's rule, not just a hint the server happens to trust."""
	if (
		deal
		and frappe.db.exists("CRM Deal", deal)
		and frappe.has_permission("CRM Deal", "read", deal, user=user)
	):
		return deal
	return None


def _call_failed_response():
	resp = VoiceResponse()
	resp.say(_("We're unable to connect your call right now. Please try again later."))
	return resp


def create_call_log(call_details: TwilioCallDetails, deal: str | None = None):
	"""One call log per Twilio call id: a /voice webhook Twilio retries (its own infrastructure
	failure, not a status change) updates the same row instead of failing on a duplicate name,
	same as every other operator (credtech#268). Linking only happens the first time."""
	details = call_details.to_dict()
	is_new = not frappe.db.exists("CRM Call Log", details["id"])
	call_log = frappe.new_doc("CRM Call Log") if is_new else frappe.get_doc("CRM Call Log", details["id"])
	call_log.update({**details, "telephony_medium": "Twilio"})

	if is_new:
		# the deal from click-to-call comes first; the number is only the fallback (credtech#47, #274)
		if deal and frappe.db.exists("CRM Deal", deal):
			call_log.reference_doctype = "CRM Deal"
			call_log.reference_docname = deal
		else:
			contact_number = details.get("from") if details.get("type") == "Incoming" else details.get("to")
			link(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def link(contact_number, call_log):
	link_call_log_to_number(call_log, contact_number)


def update_call_log(call_sid, status=None):
	"""Update call log status."""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("CRM Call Log", call_sid)):
		return

	try:
		call_details = twilio.get_call_info(call_sid)
		call_log = frappe.get_doc("CRM Call Log", call_sid)
		call_log.status = TwilioCallDetails.get_call_status(status or call_details.status)
		call_log.duration = call_details.duration
		call_log.start_time = get_datetime_from_timestamp(call_details.start_time)
		call_log.end_time = get_datetime_from_timestamp(call_details.end_time)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()


def get_twilio_settings():
	return frappe.get_single("CRM Twilio Settings")


@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	recording_url = args.RecordingUrl
	call_sid = args.CallSid
	call_log = update_call_log(call_sid)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	try:
		frappe.db.set_value("CRM Call Log", call_sid, "recording_url", recording_url)
		frappe.db.commit()
	except Exception as exc:
		frappe.log_error(title=_("Failed to capture Twilio recording"))
		raise exc


@frappe.whitelist(allow_guest=True)
def update_call_status_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	parent_call_sid = args.ParentCallSid
	call_log = update_call_log(parent_call_sid, status=args.CallStatus)
	if not call_log:
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	call_info = {
		"ParentCallSid": args.ParentCallSid,
		"CallSid": args.CallSid,
		"CallStatus": args.CallStatus,
		"CallDuration": args.CallDuration,
		"From": args.From,
		"To": args.To,
	}

	try:
		client = Twilio.get_twilio_client()
		client.calls(args.ParentCallSid).user_defined_messages.create(content=json.dumps(call_info))
	except Exception as exc:
		frappe.log_error(title=_("Failed to update Twilio call status"))
		raise exc


def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from zoneinfo import ZoneInfo

	if not timestamp:
		return None

	datetime_utc_tz_str = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, "%Y-%m-%d %H:%M:%S%z")
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(ZoneInfo(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, "yyyy-MM-dd HH:mm:ss")
