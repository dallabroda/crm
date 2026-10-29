"""Wavix adapter and webhook (credtech#271): the `post-call` payload in the common call format,
and the webhook receiver (secret in the URL, since Wavix signs nothing of its own).

Reference: https://wavix.github.io/wavix-openapi/wavix-api.yaml (`CallStatusWebhook`)."""

from unittest.mock import patch

import frappe
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.fcrm.doctype.crm_wavix_settings import crm_wavix_settings
from crm.integrations.voip import wavix as adapter
from crm.integrations.voip import webhook
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SECRET = "s3cret-for-tests"

# CallStatusWebhook, exactly as Wavix's own doc shapes it
DOC_FIXTURE = {
	"direction": "outbound",
	"uuid": "99df5ffd-962a-410f-bcce-d08f1f7f328c",
	"destination": "Brazil",
	"duration": 17,
	"charge": "0.822",
	"date": "2026-10-29T14:30:34.000Z",
	"disposition": "answered",
	"from": "554800000000",
	"to": "554833328530",
	"per_minute": "0.027",
}

# an on-call ("Call") shaped payload, which this webhook is never registered for (credtech#271)
ON_CALL_FIXTURE = {
	"uuid": "99df5ffd-962a-410f-bcce-d08f1f7f328c",
	"id": "99df5ffd-962a-410f-bcce-d08f1f7f328c",
	"direction": "outbound",
	"event_type": "call_setup",
	"event_time": "2026-10-29T14:30:00.000Z",
	"event_payload": None,
	"from": "554800000000",
	"to": "554833328530",
	"call_started": "2026-10-29T14:30:00.000Z",
	"call_answered": None,
	"call_completed": None,
	"machine_detected": False,
	"tag": "",
}


def post_call(**overrides):
	return {**DOC_FIXTURE, **overrides}


class TestWavixAdapter(FrappeTestCase):
	def setUp(self):
		self.no_recording = patch.object(adapter, "resolve_recording_url", return_value=None)
		self.no_recording.start()

	def tearDown(self):
		self.no_recording.stop()

	def test_doc_fixture(self):
		call = adapter.parse_post_call(post_call())
		self.assertEqual(
			(call["id"], call["type"], call["number"], call["status"], call["duration"], call["extension"]),
			(DOC_FIXTURE["uuid"], "Outgoing", "554833328530", "Completed", 17, None),
		)

	def test_incoming_call_uses_the_from_number(self):
		call = adapter.parse_post_call(post_call(direction="inbound"))
		self.assertEqual((call["type"], call["number"]), ("Incoming", "554800000000"))

	def test_status_mapping(self):
		for disposition, status in (
			("answered", "Completed"),
			("noanswer", "No Answer"),
			("busy", "Busy"),
			("failed", "Failed"),
			("something-new", "Failed"),
		):
			with self.subTest(disposition=disposition):
				self.assertEqual(
					adapter.parse_post_call(post_call(disposition=disposition))["status"], status
				)

	def test_is_call_event_tells_post_call_from_on_call(self):
		operator = adapter.Wavix()
		self.assertTrue(operator.is_call_event(DOC_FIXTURE))
		self.assertFalse(operator.is_call_event(ON_CALL_FIXTURE))
		self.assertFalse(operator.is_call_event({}))

	def test_cannot_originate_or_poll_yet(self):
		# click-to-call needs the Wavix Embeddable widget's JS API confirmed first (credtech#271)
		operator = adapter.Wavix()
		self.assertFalse(operator.can_originate)
		self.assertFalse(operator.polls)


class TestWavixWebhook(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		settings = frappe.get_single("CRM Wavix Settings")
		settings.update({"enabled": 1, "api_key": "key-for-tests", "webhook_secret": SECRET})
		with patch("crm.fcrm.doctype.crm_wavix_settings.crm_wavix_settings.register_webhook"):
			settings.save()

		self.recording = patch.object(adapter, "resolve_recording_url", return_value=None)
		self.recording.start()
		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		self.recording.stop()
		frappe.local.request = None
		frappe.db.rollback()

	def post(self, payload, key=SECRET):
		builder = EnvironBuilder(
			method="POST",
			path="/api/method/crm.integrations.voip.webhook.wavix",
			query_string={"key": key} if key is not None else None,
			json=payload,
		)
		frappe.local.request = Request(builder.get_environ())
		return webhook.wavix(**payload)

	def test_missing_or_wrong_secret_is_refused(self):
		for key in (None, "", "wrong"):
			with self.subTest(key=key), self.assertRaises(frappe.PermissionError):
				self.post(post_call(), key=key)

	def test_disabled_integration_is_refused(self):
		frappe.db.set_single_value("CRM Wavix Settings", "enabled", 0)
		with self.assertRaises(frappe.PermissionError):
			self.post(post_call())

	def test_secret_never_reaches_the_integration_request(self):
		self.post(post_call(uuid="secret-check"))

		request = frappe.get_last_doc("Integration Request", {"integration_request_service": "Wavix"})
		self.assertIn("secret-check", request.data)
		self.assertNotIn(SECRET, (request.data or "") + (request.request_headers or ""))
		self.assertEqual(request.status, "Completed")

	def test_on_call_shaped_payload_is_ignored(self):
		self.post(ON_CALL_FIXTURE)
		self.assertFalse(frappe.db.exists("CRM Call Log", ON_CALL_FIXTURE["uuid"]))

	def test_call_lands_on_the_open_deal_of_the_number(self):
		deal = make_deal("+55 48 3332-8530")
		self.post(post_call(uuid="call-1", to="+554833328530"))

		log = frappe.get_doc("CRM Call Log", "call-1")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))
		self.assertEqual(log.telephony_medium, "Wavix")

	def test_unknown_number_only_stays_in_the_call_history(self):
		self.post(post_call(uuid="call-2", to="+554800009999"))

		log = frappe.get_doc("CRM Call Log", "call-2")
		self.assertIsNone(log.reference_docname)
		self.assertEqual(log.links, [])

	def test_repeated_delivery_updates_the_same_call(self):
		self.post(post_call(uuid="call-3"))
		self.post(post_call(uuid="call-3", disposition="busy"))

		self.assertEqual(frappe.db.count("CRM Call Log", {"name": "call-3"}), 1)
		self.assertEqual(frappe.get_doc("CRM Call Log", "call-3").status, "Busy")

	def test_recording_url_is_resolved_and_stored(self):
		# nests on top of the setUp patch, which is restored once this block exits
		with patch.object(adapter, "resolve_recording_url", return_value="https://x/a.mp3") as resolve:
			self.post(post_call(uuid="call-4"))
		resolve.assert_called_once_with("call-4")
		self.assertEqual(frappe.get_doc("CRM Call Log", "call-4").recording_url, "https://x/a.mp3")
