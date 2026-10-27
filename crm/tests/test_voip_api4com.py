from unittest.mock import patch

import frappe
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.integrations.voip import api4com as adapter
from crm.integrations.voip import webhook
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests import default_test_pipeline

SECRET = "s3cret-for-tests"

# channel-hangup v1.4 exactly as in https://developers.api4com.com/integration-own-webphone.html
DOC_FIXTURE = {
	"version": "v1.4",
	"eventType": "channel-hangup",
	"id": "2ee13fa4-975c-499d-bbb8-5177ff418316",
	"domain": "seudominio.api4com.com",
	"direction": "outbound",
	"caller": "1000",
	"called": "04833328530",
	"startedAt": "2025-01-01 00:00:00",
	"answeredAt": "2025-01-01 00:00:05",
	"endedAt": "2025-01-01 00:00:10",
	"duration": 5,
	"hangupCause": "NORMAL_CLEARING",
	"hangupCauseCode": "16",
	"recordUrl": "https://listener.api4com.com/files/listen/2ee13fa4-975c-499d-bbb8-5177ff418316.mp3",
	"metadata": {"gateway": "integration-test", "userId": 123, "entityId": 456},
}


def hangup(**overrides):
	return {**DOC_FIXTURE, **overrides}


class TestAPI4ComAdapter(FrappeTestCase):
	def test_doc_fixture(self):
		call = adapter.parse_hangup(DOC_FIXTURE)

		self.assertEqual(call["id"], "2ee13fa4-975c-499d-bbb8-5177ff418316")
		self.assertEqual(call["type"], "Outgoing")
		self.assertEqual((call["extension"], call["number"]), ("1000", "04833328530"))
		self.assertEqual(call["status"], "Completed")
		self.assertEqual(call["duration"], 5)
		self.assertEqual(str(call["start_time"]), "2025-01-01 00:00:00")
		self.assertEqual(call["recording_url"], DOC_FIXTURE["recordUrl"])
		self.assertEqual(call["deal"], "456")

	def test_incoming_with_customer_as_caller_is_swapped(self):
		call = adapter.parse_hangup(hangup(direction="inbound", caller="+5548999998888", called="1000"))

		self.assertEqual(call["type"], "Incoming")
		self.assertEqual((call["extension"], call["number"]), ("1000", "+5548999998888"))

	def test_status_of_unanswered_calls(self):
		for cause, status in (
			("USER_BUSY", "Busy"),
			("NO_ANSWER", "No Answer"),
			("ORIGINATOR_CANCEL", "No Answer"),
			("NORMAL_CLEARING", "No Answer"),
			("CALL_REJECTED", "Failed"),
			("", "Failed"),
		):
			with self.subTest(cause=cause):
				self.assertEqual(adapter.call_status({"answeredAt": "", "hangupCause": cause}), status)

	def test_missing_or_bad_values(self):
		call = adapter.parse_hangup({"id": 7, "startedAt": "not a date", "metadata": "x"})

		self.assertEqual(call["id"], "7")
		self.assertIsNone(call["start_time"])
		self.assertIsNone(call["deal"])
		self.assertEqual(call["duration"], 0)


class TestAPI4ComWebhook(FrappeTestCase):
	def setUp(self):
		frappe.db.set_single_value("System Settings", "country", "Brazil")
		settings = frappe.get_single("CRM API4Com Settings")
		settings.update(
			{
				"enabled": 1,
				"api_token": "token",
				"webhook_secret": SECRET,
				"pipeline": default_test_pipeline(),
			}
		)
		settings.save()
		if not frappe.db.exists("CRM Telephony Agent", "Administrator"):
			frappe.get_doc({"doctype": "CRM Telephony Agent", "user": "Administrator"}).insert()
		frappe.db.set_value("CRM Telephony Agent", "Administrator", "api4com_extension", "1000")
		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.local.request = None
		frappe.db.rollback()

	def post(self, payload, key=SECRET):
		builder = EnvironBuilder(
			method="POST",
			path="/api/method/crm.integrations.voip.webhook.api4com",
			query_string={"key": key} if key is not None else None,
			json=payload,
		)
		frappe.local.request = Request(builder.get_environ())
		return webhook.api4com(**payload)

	def test_missing_or_wrong_secret_is_refused(self):
		for key in (None, "", "wrong"):
			with self.subTest(key=key), self.assertRaises(frappe.PermissionError):
				self.post(hangup(), key=key)

	def test_disabled_integration_is_refused(self):
		frappe.db.set_single_value("CRM API4Com Settings", "enabled", 0)

		with self.assertRaises(frappe.PermissionError):
			self.post(hangup())

	def test_secret_never_reaches_the_integration_request(self):
		self.post(hangup(id="secret-check"))

		request = frappe.get_last_doc("Integration Request", {"integration_request_service": "API4Com"})
		self.assertIn("secret-check", request.data)
		self.assertNotIn(SECRET, (request.data or "") + (request.request_headers or ""))
		self.assertEqual(request.status, "Completed")

	def test_other_events_are_ignored(self):
		self.post(hangup(id="answer-1", eventType="channel-answer"))

		self.assertFalse(frappe.db.exists("CRM Call Log", "answer-1"))

	def test_click_to_call_lands_on_its_deal(self):
		deal = make_deal("+55 48 3332-8530")

		self.post(hangup(id="click-1", metadata={"gateway": "integration-test", "entityId": deal}))

		log = frappe.get_doc("CRM Call Log", "click-1")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))
		self.assertEqual((log.type, log.status, log.telephony_medium), ("Outgoing", "Completed", "API4Com"))
		self.assertEqual((log.get("from"), log.to, log.caller), ("1000", "04833328530", "Administrator"))
		self.assertEqual(log.recording_url, DOC_FIXTURE["recordUrl"])

	def test_repeated_delivery_updates_the_same_call(self):
		deal = make_deal("+55 48 3332-8530")
		self.post(hangup(id="repeat-1", recordUrl="", metadata={"entityId": deal}))

		self.post(hangup(id="repeat-1", metadata={"entityId": deal}))

		self.assertEqual(frappe.db.count("CRM Call Log", {"id": "repeat-1"}), 1)
		self.assertEqual(frappe.db.get_value("CRM Call Log", "repeat-1", "reference_docname"), deal)
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", "repeat-1", "recording_url"), DOC_FIXTURE["recordUrl"]
		)

	def test_unknown_number_only_stays_in_the_call_history(self):
		"""Owner rule (credtech#47): a call never opens a deal"""
		deals, leads = frappe.db.count("CRM Deal"), frappe.db.count("CRM Lead")

		self.post(hangup(id="unknown-1", called="+55 21 98888-1234", metadata={}))

		log = frappe.get_doc("CRM Call Log", "unknown-1")
		self.assertIsNone(log.reference_docname)
		self.assertEqual(log.links, [])
		self.assertEqual((frappe.db.count("CRM Deal"), frappe.db.count("CRM Lead")), (deals, leads))

	def test_call_goes_on_every_open_deal_of_the_number(self):
		first = make_deal("+55 48 99999-7777")
		contact = frappe.db.get_value("CRM Contacts", {"parent": first}, "contact")
		second = make_deal(contact=contact)

		self.post(
			hangup(id="two-deals", direction="inbound", caller="5548999997777", called="1000", metadata={})
		)

		log = frappe.get_doc("CRM Call Log", "two-deals")
		linked = {log.reference_docname} | {link.link_name for link in log.links}
		self.assertEqual(linked, {first, second})
		self.assertNotIn(log.reference_docname, {link.link_name for link in log.links})
		self.assertEqual((log.type, log.receiver), ("Incoming", "Administrator"))

	def test_contact_with_only_closed_deals_gets_the_call_on_the_contact(self):
		closed = make_deal("+55 48 97777-1111")
		pipeline = frappe.db.get_value("CRM Deal", closed, "pipeline")
		won = frappe.get_all("CRM Deal Status", {"pipeline": pipeline, "type": "Won"}, pluck="name", limit=1)[
			0
		]
		frappe.db.set_value("CRM Deal", closed, "status", won)
		contact = frappe.db.get_value("CRM Contacts", {"parent": closed}, "contact")
		deals = frappe.db.count("CRM Deal")

		self.post(hangup(id="closed-only", called="048 97777-1111", metadata={}))

		log = frappe.get_doc("CRM Call Log", "closed-only")
		self.assertIsNone(log.reference_docname)
		self.assertEqual([(link.link_doctype, link.link_name) for link in log.links], [("Contact", contact)])
		self.assertEqual(frappe.db.count("CRM Deal"), deals)


def make_deal(phone: str | None = None, contact: str | None = None) -> str:
	if not contact:
		contact = (
			frappe.get_doc(
				{
					"doctype": "Contact",
					"first_name": "Caller",
					"phone_nos": [{"phone": phone, "is_primary_mobile_no": 1}],
				}
			)
			.insert()
			.name
		)
	deal = frappe.get_doc(
		{"doctype": "CRM Deal", "pipeline": default_test_pipeline(), "deal_owner": "Administrator"}
	)
	deal.append("contacts", {"contact": contact, "is_primary": 1})
	return deal.insert().name
