"""Click-to-call and linking for Twilio (credtech#274): the deal sent from the browser comes
first, the phone number (Brazilian or international) is only the fallback (credtech#47)."""

from unittest.mock import patch

import frappe
from frappe.utils.password import set_encrypted_password
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.integrations.twilio import api as twilio_api
from crm.integrations.twilio.twilio_handler import Twilio
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SALES_USER = "crm.user1@example.com"
ACCOUNT_SID = "AC00000000000000000000000000000001"
APPLICATION_SID = "AP00000000000000000000000000000001"


def outgoing_call(**overrides):
	"""An outgoing call's POST to /voice, exactly as Twilio sends it (their field names)."""
	return {
		"AccountSid": ACCOUNT_SID,
		"ApplicationSid": APPLICATION_SID,
		"CallSid": "CA00000000000000000000000000000001",
		"CallStatus": "in-progress",
		"Caller": f"client:{Twilio.safe_identity(SALES_USER)}",
		"To": "+554833328530",
		**overrides,
	}


class TestTwilioClickToCall(FrappeTestCase):
	"""Not run against a real Twilio account (credtech#274, owner's decision): the webhook is
	simulated with payloads shaped like Twilio's own doc."""

	def setUp(self):
		frappe.set_user("Administrator")
		# written straight to the DB, not through settings.save(): that calls the real Twilio API
		# to validate the account and fetch/create its API key and TwiML app (credtech#274)
		frappe.db.set_single_value(
			"CRM Twilio Settings",
			{
				"enabled": 1,
				"account_sid": ACCOUNT_SID,
				"twiml_sid": APPLICATION_SID,
				"api_key": "key-for-tests",
			},
		)
		set_encrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "secret-for-tests", "api_secret")
		set_encrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "token-for-tests", "auth_token")

		if not frappe.db.exists("CRM Telephony Agent", SALES_USER):
			frappe.get_doc({"doctype": "CRM Telephony Agent", "user": SALES_USER}).insert()
		frappe.db.set_value("CRM Telephony Agent", SALES_USER, "twilio_number", "+15551234567")

		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.local.request = None
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def post(self, payload):
		builder = EnvironBuilder(
			method="POST",
			path="/api/method/crm.integrations.twilio.api.voice",
			data=payload,
		)
		frappe.local.request = Request(builder.get_environ())
		return twilio_api.voice(**payload)

	def test_wrong_account_is_refused(self):
		with self.assertRaises(frappe.PermissionError):
			self.post(outgoing_call(AccountSid="wrong"))

	def test_wrong_application_is_refused(self):
		with self.assertRaises(frappe.PermissionError):
			self.post(outgoing_call(ApplicationSid="wrong"))

	def test_agent_without_a_number_is_told_so(self):
		frappe.db.set_value("CRM Telephony Agent", SALES_USER, "twilio_number", "")
		resp = self.post(outgoing_call())
		self.assertIn(b"administrator", resp.get_data())

	def test_click_to_call_lands_on_its_deal(self):
		deal = make_deal("+1 415 555 0132")  # the number plays no part: the deal id wins
		self.post(outgoing_call(CallSid="click-1", DealId=deal))

		log = frappe.get_doc("CRM Call Log", "click-1")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))
		self.assertEqual(log.telephony_medium, "Twilio")

	def test_deal_that_does_not_exist_falls_back_to_the_number(self):
		deal = make_deal("+55 48 3332-8530")
		self.post(outgoing_call(CallSid="click-2", To="+554833328530", DealId="does-not-exist"))

		log = frappe.get_doc("CRM Call Log", "click-2")
		self.assertIsNone(log.reference_docname)
		self.assertTrue(log.has_link("CRM Deal", deal))

	def test_no_deal_id_falls_back_to_the_brazilian_number(self):
		deal = make_deal("(48) 99999-8530")
		self.post(outgoing_call(CallSid="br-1", To="+5548999998530"))

		log = frappe.get_doc("CRM Call Log", "br-1")
		self.assertTrue(log.has_link("CRM Deal", deal))

	def test_no_deal_id_falls_back_to_an_international_number(self):
		"""The number lookup already supports non-Brazilian numbers via their own country code
		(credtech#274): no change was needed in the lookup itself, just this coverage."""
		deal = make_deal("+1 (415) 555-0132")
		self.post(outgoing_call(CallSid="us-1", To="+14155550132"))

		log = frappe.get_doc("CRM Call Log", "us-1")
		self.assertTrue(log.has_link("CRM Deal", deal))

	def test_unknown_number_only_stays_in_the_call_history(self):
		self.post(outgoing_call(CallSid="unknown-1", To="+14155559999"))

		log = frappe.get_doc("CRM Call Log", "unknown-1")
		self.assertIsNone(log.reference_docname)
		self.assertEqual(log.links, [])

	def test_repeated_delivery_updates_the_same_call(self):
		deal = make_deal("+1 415 555 0199")
		self.post(outgoing_call(CallSid="repeat-1", DealId=deal))
		self.post(outgoing_call(CallSid="repeat-1", CallStatus="completed", DealId=deal))

		self.assertEqual(frappe.db.count("CRM Call Log", {"name": "repeat-1"}), 1)
