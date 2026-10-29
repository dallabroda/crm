"""Telnyx adapter (credtech#270): click-to-call in two legs, signed webhooks, recordings fetched fresh.
Payloads follow the Call Control OpenAPI spec (`call-control.json`). Not run against a real account."""

import base64
import json
import time
from unittest.mock import MagicMock, patch

import frappe
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.integrations import api as integrations_api
from crm.integrations.voip import telnyx, webhook
from crm.integrations.voip.operators import get_operator, get_operator_by_medium
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SECRET = "telnyx-secret-for-tests"
SIGNING_KEY = Ed25519PrivateKey.generate()
PUBLIC_KEY = base64.b64encode(SIGNING_KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
SALESPERSON = "+5548999990000"


def response(status=200, body=None):
	mock = MagicMock(status_code=status, text=json.dumps(body or {}))
	mock.json.return_value = body or {}
	return mock


def event(event_type, state, **payload):
	"""A Call Control webhook as in call-control.json (CallHangup, CallAnswered, CallRecordingSaved)."""
	return {
		"data": {
			"record_type": "event",
			"event_type": event_type,
			"id": "0ccc7b54-4df3-4bca-a65a-3da1ecc777f0",
			"occurred_at": "2026-10-29T22:25:27.521992Z",
			"payload": {
				"call_control_id": "v3:MdI91X4lWFEs7IgbBEOT9M4AigoY08M0WWZFISt1Yw2axZ_IiE4pqg",
				"connection_id": "7267xxxxxxxxxxxxxx",
				"call_leg_id": "428c31b6-7af4-4bcb-b7f5-5013ef9657c1",
				"call_session_id": "428c31b6-abf3-3bc1-b7f4-5013ef9657c1",
				"client_state": telnyx.encode_state(state) if state else None,
				"from": "+554830000000",
				"to": "+5548988887777",
				"start_time": "2026-10-29T22:24:27.521992Z",
				**payload,
			},
		},
		"meta": {"attempt": 1, "delivered_to": "https://example.com"},
	}


def state(leg="customer", deal=None, call_id="telnyx-abc123"):
	return {"id": call_id, "leg": leg, "deal": deal, "extension": SALESPERSON, "number": "+5548988887777"}


def settings():
	s = frappe.get_single("CRM Telnyx Settings")
	s.update(
		{
			"enabled": 1,
			"api_key": "KEY-for-tests",
			"connection_id": "7267xxxxxxxxxxxxxx",
			"caller_number": "+554830000000",
			"public_key": PUBLIC_KEY,
			"webhook_secret": SECRET,
		}
	)
	return s


class TestTelnyxOperator(FrappeTestCase):
	def test_registered_and_originates_without_polling(self):
		op = get_operator("telnyx")
		self.assertIs(op, get_operator_by_medium("Telnyx"))
		self.assertTrue(op.can_originate)
		self.assertFalse(op.polls)

	def test_extension_is_a_phone_or_sip_address(self):
		op = telnyx.Telnyx()
		op.validate_extension(SALESPERSON)
		op.validate_extension("sip:ana@acme.sip.telnyx.com")
		for bad in ("1000", "48999990000", "sip:ana", ""):
			with self.subTest(bad=bad), self.assertRaises(frappe.ValidationError):
				op.validate_extension(bad)

	def test_numbers_go_out_in_e164(self):
		self.assertEqual(telnyx.to_e164("(48) 98888-7777"), "+5548988887777")
		self.assertEqual(telnyx.to_e164("+1 312 945 7420"), "+13129457420")
		self.assertEqual(telnyx.to_e164("5548988887777"), "+5548988887777")

	def test_foreign_client_state_is_ignored(self):
		self.assertIsNone(telnyx.decode_state(None))
		self.assertIsNone(telnyx.decode_state("not base64 !"))
		self.assertIsNone(telnyx.decode_state(base64.b64encode(b'{"id": "other-app"}').decode()))
		self.assertEqual(telnyx.decode_state(telnyx.encode_state(state()))["id"], "telnyx-abc123")


class TestTelnyxClickToCall(FrappeTestCase):
	def test_rings_the_salesperson_first_with_the_deal_in_client_state(self):
		with patch(
			"crm.integrations.voip.telnyx.requests.request", return_value=response(200, {"data": {}})
		) as call:
			call_id = telnyx.originate_call(settings(), SALESPERSON, "(48) 98888-7777", "CRM-DEAL-1")

		method, url = call.call_args.args
		body = call.call_args.kwargs["json"]
		self.assertEqual((method, url), ("post", "https://api.telnyx.com/v2/calls"))
		self.assertEqual(call.call_args.kwargs["headers"]["Authorization"], "Bearer KEY-for-tests")
		self.assertEqual(
			(body["connection_id"], body["to"], body["from"]),
			("7267xxxxxxxxxxxxxx", SALESPERSON, "+554830000000"),
		)
		self.assertIn(f"key={SECRET}", body["webhook_url"])
		sent = telnyx.decode_state(body["client_state"])
		self.assertEqual(sent["id"], call_id)
		self.assertEqual(
			(sent["leg"], sent["deal"], sent["number"]), ("agent", "CRM-DEAL-1", "+5548988887777")
		)

	def test_refusal_shows_a_readable_error(self):
		with (
			patch("crm.integrations.voip.telnyx.requests.request", return_value=response(401)),
			self.assertRaises(frappe.ValidationError) as raised,
		):
			telnyx.originate_call(settings(), SALESPERSON, "48988887777", None)
		self.assertIn("API key", str(raised.exception))

	def test_salesperson_answering_calls_the_customer_and_records(self):
		with patch("crm.integrations.voip.telnyx.requests.request", return_value=response()) as call:
			telnyx.on_answered(settings(), event("call.answered", state(leg="agent", deal="CRM-DEAL-1")))

		method, url = call.call_args.args
		body = call.call_args.kwargs["json"]
		self.assertEqual(method, "post")
		self.assertTrue(url.endswith("/actions/transfer"))
		self.assertEqual((body["to"], body["from"]), ("+5548988887777", "+554830000000"))
		self.assertEqual(body["record"], "record-from-answer")
		customer = telnyx.decode_state(body["target_leg_client_state"])
		self.assertEqual((customer["leg"], customer["deal"]), ("customer", "CRM-DEAL-1"))

	def test_only_the_salesperson_answering_triggers_the_transfer(self):
		with patch("crm.integrations.voip.telnyx.requests.request") as call:
			telnyx.on_answered(settings(), event("call.answered", state(leg="customer")))
			telnyx.on_answered(settings(), event("call.answered", None))
			telnyx.on_answered(settings(), event("call.hangup", state(leg="agent")))
		call.assert_not_called()


class TestTelnyxHangup(FrappeTestCase):
	def test_customer_leg_hangup_is_the_call(self):
		call = telnyx.call_to_record(
			event("call.hangup", state(deal="CRM-DEAL-1"), hangup_cause="normal_clearing")
		)

		self.assertEqual(call["id"], "telnyx-abc123")
		self.assertEqual(
			(call["type"], call["status"], call["deal"]), ("Outgoing", "Completed", "CRM-DEAL-1")
		)
		self.assertEqual((call["extension"], call["number"]), (SALESPERSON, "+5548988887777"))
		self.assertEqual(call["duration"], 60)
		self.assertIsNone(call["start_time"].tzinfo)

	def test_status_of_the_customer_leg(self):
		for cause, status in (("no_answer", "No Answer"), ("user_busy", "Busy"), ("call_rejected", "Failed")):
			with self.subTest(cause=cause):
				call = telnyx.call_to_record(event("call.hangup", state(), hangup_cause=cause))
				self.assertEqual(call["status"], status)

	def test_salesperson_leg_records_only_when_they_never_answered(self):
		self.assertIsNone(
			telnyx.call_to_record(event("call.hangup", state(leg="agent"), hangup_cause="normal_clearing"))
		)
		call = telnyx.call_to_record(event("call.hangup", state(leg="agent"), hangup_cause="no_answer"))
		self.assertEqual(call["status"], "Canceled")

	def test_other_events_and_other_apps_are_not_calls(self):
		self.assertIsNone(telnyx.call_to_record(event("call.answered", state())))
		self.assertIsNone(telnyx.call_to_record(event("call.hangup", None, hangup_cause="normal_clearing")))


class TestTelnyxWebhook(FrappeTestCase):
	def setUp(self):
		frappe.db.set_single_value("System Settings", "country", "Brazil")
		with patch("crm.fcrm.doctype.crm_telnyx_settings.crm_telnyx_settings.check_application"):
			settings().save()
		frappe.db.delete("CRM Telephony Extension", {"medium": "Telnyx"})
		if not frappe.db.exists("CRM Telephony Agent", "Administrator"):
			frappe.get_doc({"doctype": "CRM Telephony Agent", "user": "Administrator"}).insert()
		agent = frappe.get_doc("CRM Telephony Agent", "Administrator")
		agent.set_extension("Telnyx", SALESPERSON)
		agent.save()
		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.local.request = None
		frappe.db.rollback()

	def post(self, payload, key=SECRET, signed_with=SIGNING_KEY, timestamp=None):
		body = json.dumps(payload).encode()
		timestamp = str(timestamp or int(time.time()))
		signature = base64.b64encode(signed_with.sign(timestamp.encode() + b"|" + body)).decode()
		builder = EnvironBuilder(
			method="POST",
			path="/api/method/crm.integrations.voip.webhook.telnyx",
			query_string={"key": key} if key is not None else None,
			data=body,
			content_type="application/json",
			headers={"telnyx-signature-ed25519": signature, "telnyx-timestamp": timestamp},
		)
		frappe.local.request = Request(builder.get_environ())
		return webhook.telnyx(**payload)

	def test_wrong_secret_signature_or_old_timestamp_is_refused(self):
		payload = event("call.hangup", state(), hangup_cause="normal_clearing")
		for kwargs in (
			{"key": "wrong"},
			{"signed_with": Ed25519PrivateKey.generate()},
			{"timestamp": int(time.time()) - 600},
		):
			with (
				self.subTest(**{k: str(v) for k, v in kwargs.items()}),
				self.assertRaises(frappe.PermissionError),
			):
				self.post(payload, **kwargs)
		self.assertFalse(frappe.db.exists("CRM Call Log", "telnyx-abc123"))

	def test_click_to_call_lands_on_its_deal_in_the_salespersons_name(self):
		deal = make_deal("+55 48 98888-7777")

		self.post(event("call.hangup", state(deal=deal), hangup_cause="normal_clearing"))

		log = frappe.get_doc("CRM Call Log", "telnyx-abc123")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))
		self.assertEqual((log.type, log.status, log.telephony_medium), ("Outgoing", "Completed", "Telnyx"))
		self.assertEqual(
			(log.get("from"), log.to, log.caller), (SALESPERSON, "+5548988887777", "Administrator")
		)

	def test_answer_event_transfers_and_records_nothing(self):
		with patch("crm.integrations.voip.telnyx.requests.request", return_value=response()) as call:
			self.post(event("call.answered", state(leg="agent")))

		self.assertTrue(call.call_args.args[1].endswith("/actions/transfer"))
		self.assertFalse(frappe.db.exists("CRM Call Log", "telnyx-abc123"))

	def test_recording_saved_after_the_hangup_is_attached(self):
		self.post(event("call.hangup", state(), hangup_cause="normal_clearing"))
		found = response(
			200, {"data": [{"id": "rec-1", "call_session_id": "428c31b6-abf3-3bc1-b7f4-5013ef9657c1"}]}
		)

		with patch("crm.integrations.voip.telnyx.requests.request", return_value=found) as call:
			self.post(
				event("call.recording.saved", state(), recording_urls={"mp3": "https://s3.example/x.mp3"})
			)

		self.assertEqual(
			call.call_args.kwargs["params"],
			{"filter[call_session_id]": "428c31b6-abf3-3bc1-b7f4-5013ef9657c1"},
		)
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", "telnyx-abc123", "recording_url"),
			"https://api.telnyx.com/v2/recordings/rec-1",
		)

	def test_recording_saved_before_the_hangup_waits_for_it(self):
		found = response(200, {"data": [{"id": "rec-2"}]})
		with patch("crm.integrations.voip.telnyx.requests.request", return_value=found):
			self.post(event("call.recording.saved", state(call_id="telnyx-early")))

		self.post(event("call.hangup", state(call_id="telnyx-early"), hangup_cause="normal_clearing"))

		self.assertEqual(
			frappe.db.get_value("CRM Call Log", "telnyx-early", "recording_url"),
			"https://api.telnyx.com/v2/recordings/rec-2",
		)
		frappe.cache().delete_value(telnyx.RECORDING_CACHE_KEY.format("telnyx-early"))

	def test_recording_plays_from_a_fresh_link(self):
		self.post(event("call.hangup", state(), hangup_cause="normal_clearing"))
		frappe.db.set_value(
			"CRM Call Log", "telnyx-abc123", "recording_url", "https://api.telnyx.com/v2/recordings/rec-1"
		)
		fresh = response(200, {"data": {"download_urls": {"mp3": "https://s3.example/fresh.mp3"}}})

		with patch("crm.integrations.voip.telnyx.requests.request", return_value=fresh) as call:
			link = integrations_api._recording_location(frappe.get_doc("CRM Call Log", "telnyx-abc123"))

		self.assertEqual(link, "https://s3.example/fresh.mp3")
		self.assertEqual(call.call_args.args[1], "https://api.telnyx.com/v2/recordings/rec-1")


class TestTelnyxSettings(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_bad_caller_number_or_public_key_is_refused(self):
		for field, value in (
			("caller_number", "48 3000-0000"),
			("public_key", "not-a-key"),
			("connection_id", " "),
		):
			doc = settings()
			doc.set(field, value)
			with self.subTest(field=field), self.assertRaises(frappe.ValidationError):
				with patch("crm.fcrm.doctype.crm_telnyx_settings.crm_telnyx_settings.check_application"):
					doc.save()

	def test_key_is_checked_with_telnyx_on_save(self):
		with (
			patch("crm.integrations.voip.telnyx.requests.request", return_value=response(401)) as call,
			self.assertRaises(frappe.ValidationError),
		):
			settings().save()
		self.assertTrue(call.call_args.args[1].endswith("/call_control_applications/7267xxxxxxxxxxxxxx"))

	def test_webhook_secret_is_generated(self):
		doc = settings()
		doc.webhook_secret = None
		with patch("crm.fcrm.doctype.crm_telnyx_settings.crm_telnyx_settings.check_application"):
			doc.save()
		self.assertEqual(len(doc.get_password("webhook_secret")), 40)
