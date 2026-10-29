from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import get_datetime, now_datetime

from crm.integrations import api as integrations_api
from crm.integrations.voip import api as voip_api
from crm.integrations.voip import api4com, operators, polling
from crm.integrations.voip.base import Operator
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SALES_USER = "crm.user1@example.com"
CURSOR = "crm_voip_poll_cursor_polltest"


class PollingOperator(Operator):
	"""An operator without webhook, like Nvoip: its calls come by polling. It borrows the API4Com
	medium and settings only to have an `enabled` flag and extensions to look up."""

	key = "polltest"
	medium = "API4Com"
	settings_doctype = "CRM API4Com Settings"

	def __init__(self, calls=None, error=None):
		self.calls = calls or []
		self.error = error
		self.since = []

	def list_calls(self, settings, since):
		self.since.append(since)
		if self.error:
			raise self.error
		return self.calls


def common_call(call_id, **overrides):
	return {
		"id": call_id,
		"type": "Outgoing",
		"extension": "1000",
		"number": "+55 48 3332-8530",
		"status": "Completed",
		"start_time": get_datetime("2026-10-29 10:00:00"),
		"end_time": get_datetime("2026-10-29 10:01:00"),
		"duration": 60,
		"recording_url": None,
		"deal": None,
		**overrides,
	}


class VoipTestCase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM Telephony Extension", {"medium": "API4Com"})
		frappe.db.set_single_value("CRM API4Com Settings", "enabled", 1)
		# the code under test commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def set_extension(self, user, extension, medium="API4Com"):
		if frappe.db.exists("CRM Telephony Agent", user):
			agent = frappe.get_doc("CRM Telephony Agent", user)
		else:
			agent = frappe.new_doc("CRM Telephony Agent")
			agent.user = user
		agent.set_extension(medium, extension)
		agent.save()
		return agent


class TestOperators(VoipTestCase):
	def test_registry(self):
		self.assertIs(operators.get_operator("api4com"), operators.get_operator_by_medium("API4Com"))
		self.assertIsNone(operators.get_operator_by_medium("Twilio"))
		self.assertIsNone(operators.get_operator_by_medium(None))

	def test_capabilities_come_from_what_the_adapter_implements(self):
		self.assertTrue(api4com.API4Com().can_originate)
		self.assertFalse(api4com.API4Com().polls)
		self.assertTrue(PollingOperator().polls)
		self.assertFalse(PollingOperator().can_originate)

	def test_call_flags_for_the_screen(self):
		flags = integrations_api.is_call_integration_enabled()
		self.assertEqual(flags["voip"], {"api4com": "API4Com"})
		self.assertTrue(flags["integrations"]["api4com"])

		frappe.db.set_single_value("CRM API4Com Settings", "enabled", 0)
		flags = integrations_api.is_call_integration_enabled()
		self.assertEqual(flags["voip"], {})
		self.assertNotIn("api4com", flags["integrations"])
		# Twilio and Exotel keep their keys whatever the operators
		self.assertIn("twilio", flags["integrations"])
		self.assertIn("exotel", flags["integrations"])

	def test_recording_auth_goes_through_the_operator(self):
		self.assertIsNone(integrations_api._get_recording_credentials("API4Com"))
		self.assertIsNone(integrations_api._get_recording_credentials("Manual"))


class TestExtensions(VoipTestCase):
	def test_one_extension_per_operator_and_user(self):
		agent = self.set_extension("Administrator", "1000")
		self.assertEqual(agent.get_extension("API4Com"), "1000")
		self.set_extension("Administrator", "1001")
		agent.reload()
		self.assertEqual([(r.medium, r.extension) for r in agent.extensions], [("API4Com", "1001")])

		agent.append("extensions", {"medium": "API4Com", "extension": "1002"})
		with self.assertRaises(frappe.ValidationError):
			agent.save()

	def test_extension_belongs_to_one_user(self):
		self.set_extension("Administrator", "1000")
		with self.assertRaises(frappe.ValidationError):
			self.set_extension(SALES_USER, "1000")

	def test_unknown_operator_and_bad_extension_are_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.set_extension("Administrator", "1000", medium="Nope")
		for wrong in ("12a", "1234567"):
			agent = frappe.new_doc("CRM Telephony Agent")
			agent.user = SALES_USER
			agent.append("extensions", {"medium": "API4Com", "extension": wrong})
			with self.subTest(extension=wrong), self.assertRaises(frappe.ValidationError):
				agent.insert()

	def test_settings_screen_api(self):
		self.assertEqual(voip_api.set_extension("api4com", SALES_USER, " 2001 ")["extension"], "2001")
		self.assertEqual(voip_api.get_extensions("api4com"), {SALES_USER: "2001"})
		voip_api.set_extension("api4com", SALES_USER, "")
		self.assertEqual(voip_api.get_extensions("api4com"), {})
		with self.assertRaises(frappe.ValidationError):
			voip_api.get_extensions("nope")

	def test_salesperson_cannot_manage_extensions(self):
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			voip_api.set_extension("api4com", SALES_USER, "2001")
		with self.assertRaises(frappe.PermissionError):
			voip_api.get_extensions("api4com")

	def test_call_finds_its_salesperson_by_extension(self):
		from crm.integrations.voip.webhook import agent_of_extension

		self.set_extension(SALES_USER, "2001")
		self.assertEqual(agent_of_extension("2001", "API4Com"), SALES_USER)
		self.assertIsNone(agent_of_extension("2001", "Twilio"))
		self.assertIsNone(agent_of_extension("", "API4Com"))

	def test_migration_of_the_old_api4com_field(self):
		from crm.patches.credhub import telephony_extensions

		if not frappe.db.has_column("CRM Telephony Agent", "api4com_extension"):
			self.skipTest("site created after the field was removed")
		self.set_extension("Administrator", "1000")
		frappe.db.delete("CRM Telephony Extension", {"medium": "API4Com"})
		frappe.db.sql(
			"update `tabCRM Telephony Agent` set api4com_extension = ' 3001 ' where name = 'Administrator'"
		)
		telephony_extensions.execute()
		telephony_extensions.execute()  # run twice: no duplicate

		agent = frappe.get_doc("CRM Telephony Agent", "Administrator")
		self.assertEqual([(r.medium, r.extension) for r in agent.extensions], [("API4Com", "3001")])


class TestPolling(VoipTestCase):
	def setUp(self):
		super().setUp()
		frappe.db.delete("DefaultValue", {"defkey": CURSOR})
		frappe.clear_cache()

	def run_with(self, operator):
		with patch.dict(polling.OPERATORS, {operator.key: operator}):
			polling.poll_calls()

	def test_first_run_reads_the_last_hour_and_records_once(self):
		self.set_extension("Administrator", "1000")
		operator = PollingOperator(calls=[common_call("poll-1")])
		before = now_datetime()
		self.run_with(operator)
		self.run_with(operator)

		first, second = operator.since
		self.assertAlmostEqual((before - first).total_seconds(), 3600, delta=60)
		# next runs start at the last run, minus the overlap
		self.assertAlmostEqual((before - second).total_seconds(), polling.OVERLAP.total_seconds(), delta=60)
		self.assertEqual(frappe.db.count("CRM Call Log", {"name": "poll-1"}), 1)
		log = frappe.get_doc("CRM Call Log", "poll-1")
		self.assertEqual((log.telephony_medium, log.caller), ("API4Com", "Administrator"))

	def test_polled_call_lands_on_the_open_deal_of_the_number(self):
		deal = make_deal("+55 48 3332-8530")
		self.run_with(PollingOperator(calls=[common_call("poll-2")]))

		log = frappe.get_doc("CRM Call Log", "poll-2")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))

	def test_api_failure_keeps_the_cursor(self):
		self.run_with(PollingOperator(error=Exception("down")))
		self.assertIsNone(frappe.db.get_default(CURSOR))

	def test_one_bad_call_does_not_stop_the_others(self):
		self.run_with(PollingOperator(calls=[{"id": "broken"}, common_call("poll-3")]))
		self.assertTrue(frappe.db.exists("CRM Call Log", "poll-3"))
		self.assertIsNotNone(frappe.db.get_default(CURSOR))

	def test_disabled_operator_is_not_polled(self):
		frappe.db.set_single_value("CRM API4Com Settings", "enabled", 0)
		operator = PollingOperator(calls=[common_call("poll-4")])
		self.run_with(operator)
		self.assertEqual(operator.since, [])

	def test_webhook_operators_are_not_polled(self):
		with patch.object(polling, "poll") as poll:
			polling.poll_calls()
		poll.assert_not_called()


class TestClickToCall(VoipTestCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_single("CRM API4Com Settings")
		settings.api_token = "token-for-tests"
		with patch("crm.fcrm.doctype.crm_api4com_settings.crm_api4com_settings.register_webhook"):
			settings.save()
		self.post = patch.object(
			api4com.requests,
			"post",
			return_value=MagicMock(status_code=200, json=lambda: {"id": "call-9"}, text="{}"),
		)
		self.api4com = self.post.start()

	def tearDown(self):
		self.post.stop()
		super().tearDown()

	def test_rings_the_extension_and_sends_the_deal(self):
		self.set_extension("Administrator", "1000")
		deal = make_deal("+55 48 3332-8530")

		result = voip_api.make_call("+5548333328530", deal=deal)

		self.assertEqual(result, {"medium": "API4Com", "id": "call-9"})
		sent = self.api4com.call_args
		self.assertEqual(sent.args[0], "https://api.api4com.com/api/v1/calls")
		self.assertEqual(
			sent.kwargs["json"],
			{
				"extension": "1000",
				"caller": "1000",
				"called": "+5548333328530",
				"metadata": {"gateway": "cred-hub", "entityId": deal},
			},
		)
		self.assertEqual(sent.kwargs["headers"], {"Authorization": "token-for-tests"})

	def test_deal_that_does_not_exist_is_not_sent(self):
		self.set_extension("Administrator", "1000")
		voip_api.make_call("+5548333328530", deal="does-not-exist")
		self.assertNotIn("entityId", self.api4com.call_args.kwargs["json"]["metadata"])

	def test_needs_an_extension(self):
		with self.assertRaises(frappe.ValidationError):
			voip_api.make_call("+5548333328530")
		self.api4com.assert_not_called()

	def test_needs_an_enabled_operator(self):
		self.set_extension("Administrator", "1000")
		frappe.db.set_single_value("CRM API4Com Settings", "enabled", 0)
		with self.assertRaises(frappe.ValidationError):
			voip_api.make_call("+5548333328530")
		self.api4com.assert_not_called()

	def test_refusal_is_explained(self):
		self.set_extension("Administrator", "1000")
		self.api4com.return_value = MagicMock(status_code=424, text="offline")
		with self.assertRaises(frappe.ValidationError) as raised:
			voip_api.make_call("+5548333328530")
		self.assertIn("webphone", str(raised.exception))
