"""Nvoip adapter (credtech#269): token caching, click-to-call tracked by `CRM Nvoip Pending Call`,
polling of outbound outcomes and inbound history. Not run against a real account."""

from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import add_to_date, now_datetime

from crm.integrations.voip import nvoip
from crm.integrations.voip.operators import get_operator, get_operator_by_medium
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SALES_USER = "crm.user1@example.com"


def nvoip_settings():
	s = frappe.get_single("CRM Nvoip Settings")
	s.enabled = 1
	s.numbersip = "558400000000"
	s.user_token = "token-for-tests"
	return s


def cache_a_token(ttl_seconds=3600):
	frappe.cache().set_value(
		nvoip.TOKEN_CACHE_KEY,
		{"access_token": "cached-token", "expires_at": str(add_to_date(now_datetime(), seconds=ttl_seconds))},
	)


class TestNvoipOperator(FrappeTestCase):
	def test_registered_and_both_polls_and_originates(self):
		op = get_operator("nvoip")
		self.assertIs(op, get_operator_by_medium("Nvoip"))
		self.assertTrue(op.polls)
		self.assertTrue(op.can_originate)

	def test_extension_pattern(self):
		op = nvoip.Nvoip()
		op.validate_extension("12345")
		with self.assertRaises(frappe.ValidationError):
			op.validate_extension("12a")
		with self.assertRaises(frappe.ValidationError):
			op.validate_extension("")

	def test_agent_can_pick_nvoip_as_the_default_medium(self):
		frappe.set_user("Administrator")
		if frappe.db.exists("CRM Telephony Agent", SALES_USER):
			agent = frappe.get_doc("CRM Telephony Agent", SALES_USER)
		else:
			agent = frappe.new_doc("CRM Telephony Agent")
			agent.user = SALES_USER
		agent.default_medium = "Nvoip"
		agent.save()
		frappe.db.rollback()


class TestNvoipTokens(FrappeTestCase):
	def setUp(self):
		frappe.cache().delete_value(nvoip.TOKEN_CACHE_KEY)

	def tearDown(self):
		frappe.cache().delete_value(nvoip.TOKEN_CACHE_KEY)

	def test_password_grant_is_cached(self):
		token_response = MagicMock(
			status_code=200,
			json=lambda: {"access_token": "tok1", "refresh_token": "r", "expires_in": 86399},
		)
		with patch.object(nvoip.requests, "post", return_value=token_response) as post:
			first = nvoip._access_token(nvoip_settings())
			second = nvoip._access_token(nvoip_settings())
		self.assertEqual((first, second), ("tok1", "tok1"))
		post.assert_called_once()  # the second call reused the cache

	def test_expired_token_is_requested_again(self):
		frappe.cache().set_value(
			nvoip.TOKEN_CACHE_KEY,
			{"access_token": "stale", "expires_at": str(add_to_date(now_datetime(), seconds=-10))},
		)
		fresh = MagicMock(status_code=200, json=lambda: {"access_token": "fresh", "expires_in": 86399})
		with patch.object(nvoip.requests, "post", return_value=fresh):
			self.assertEqual(nvoip._access_token(nvoip_settings()), "fresh")

	def test_wrong_credentials_are_refused(self):
		with patch.object(nvoip.requests, "post", return_value=MagicMock(status_code=401, text="")):
			with self.assertRaises(frappe.ValidationError):
				nvoip._access_token(nvoip_settings())

	def test_a_401_on_a_call_forces_a_fresh_token(self):
		cache_a_token()
		fresh_token = MagicMock(status_code=200, json=lambda: {"access_token": "fresh", "expires_in": 86399})
		responses = [
			MagicMock(status_code=401, text=""),
			MagicMock(status_code=200, json=lambda: {"state": "finished"}),
		]
		with (
			patch.object(nvoip.requests, "request", side_effect=responses) as request,
			patch.object(nvoip.requests, "post", return_value=fresh_token),
		):
			response = nvoip._request(nvoip_settings(), "get", "/calls", params={"callId": "x"})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(request.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer fresh")


class TestNvoipClickToCall(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM Nvoip Pending Call")
		cache_a_token()
		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.cache().delete_value(nvoip.TOKEN_CACHE_KEY)
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_originate_call_tracks_the_deal_extension_and_number(self):
		deal = make_deal("+55 48 3332-8530")
		ok = MagicMock(status_code=200, json=lambda: {"state": "success", "callId": "c-1"})
		with patch.object(nvoip.requests, "request", return_value=ok):
			call_id = nvoip.originate_call(nvoip_settings(), "1000", "+5548333328530", deal)

		self.assertEqual(call_id, "c-1")
		pending = frappe.get_doc("CRM Nvoip Pending Call", "c-1")
		self.assertEqual((pending.deal, pending.extension, pending.number), (deal, "1000", "+5548333328530"))

	def test_originate_call_strips_the_country_code(self):
		ok = MagicMock(status_code=200, json=lambda: {"callId": "c-2"})
		with patch.object(nvoip.requests, "request", return_value=ok) as request:
			nvoip.originate_call(nvoip_settings(), "1000", "+55 48 3332-8530", None)
		self.assertEqual(request.call_args.kwargs["json"], {"caller": "1000", "called": "4833328530"})

	def test_refused_call_is_explained_and_not_tracked(self):
		with patch.object(nvoip.requests, "request", return_value=MagicMock(status_code=401, text="")):
			with self.assertRaises(frappe.ValidationError):
				nvoip.originate_call(nvoip_settings(), "1000", "+5548333328530", None)
		self.assertEqual(frappe.db.count("CRM Nvoip Pending Call"), 0)

	def test_talking_call_is_read_again_next_run(self):
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": "talk-1",
				"extension": "1000",
				"number": "+5548333328530",
			}
		).insert()
		talking = MagicMock(status_code=200, json=lambda: {"state": "established"})
		with patch.object(nvoip.requests, "request", return_value=talking):
			calls = nvoip.poll_pending_calls(nvoip_settings())

		self.assertEqual(calls, [])
		self.assertTrue(frappe.db.exists("CRM Nvoip Pending Call", "talk-1"))

	def test_finished_call_is_returned_but_the_pending_row_waits_for_confirmation(self):
		"""review of crm#71: the row is not deleted here. `poll()` (polling.py) records the call
		separately, and its commit would otherwise also commit this deletion even if a different
		call in the same batch then fails to record — losing it for good."""
		deal = make_deal("+1 415 555 0132")
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": "fin-1",
				"deal": deal,
				"extension": "1000",
				"number": "+14155550132",
			}
		).insert()
		finished = MagicMock(
			status_code=200,
			json=lambda: {"state": "finished", "talkingDurationSeconds": 42, "linkAudio": "https://x/a.mp3"},
		)
		with patch.object(nvoip.requests, "request", return_value=finished):
			calls = nvoip.poll_pending_calls(nvoip_settings())

		self.assertEqual(len(calls), 1)
		call = calls[0]
		self.assertEqual(
			(call["id"], call["type"], call["status"], call["duration"], call["deal"], call["recording_url"]),
			("fin-1", "Outgoing", "Completed", 42, deal, "https://x/a.mp3"),
		)
		self.assertTrue(frappe.db.exists("CRM Nvoip Pending Call", "fin-1"))

	def test_pending_row_is_dropped_once_the_call_log_confirms_it_was_recorded(self):
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": "fin-2",
				"extension": "1000",
				"number": "+14155550132",
			}
		).insert()
		frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": "fin-2",
				"type": "Outgoing",
				"status": "Completed",
				"from": "1000",
				"to": "+14155550132",
				"telephony_medium": "Nvoip",
			}
		).insert()

		with patch.object(nvoip.requests, "request", side_effect=AssertionError) as request:
			calls = nvoip.poll_pending_calls(nvoip_settings())

		self.assertEqual(calls, [])
		self.assertFalse(frappe.db.exists("CRM Nvoip Pending Call", "fin-2"))
		request.assert_not_called()  # already recorded: no need to ask Nvoip again

	def test_pending_call_that_keeps_failing_is_given_up_after_a_day(self):
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": "stuck-1",
				"extension": "1000",
				"number": "+5548333328530",
			}
		).insert()
		frappe.db.set_value(
			"CRM Nvoip Pending Call",
			"stuck-1",
			"creation",
			add_to_date(now_datetime(), days=-2),
			update_modified=False,
		)
		broken = MagicMock(status_code=404, text="")
		with patch.object(nvoip.requests, "request", return_value=broken):
			calls = nvoip.poll_pending_calls(nvoip_settings())

		self.assertEqual(calls, [])
		self.assertFalse(frappe.db.exists("CRM Nvoip Pending Call", "stuck-1"))

	def test_pending_call_failing_for_less_than_a_day_is_kept(self):
		frappe.get_doc(
			{
				"doctype": "CRM Nvoip Pending Call",
				"call_id": "retry-1",
				"extension": "1000",
				"number": "+5548333328530",
			}
		).insert()
		broken = MagicMock(status_code=404, text="")
		with patch.object(nvoip.requests, "request", return_value=broken):
			calls = nvoip.poll_pending_calls(nvoip_settings())

		self.assertEqual(calls, [])
		self.assertTrue(frappe.db.exists("CRM Nvoip Pending Call", "retry-1"))


class TestNvoipHistory(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		cache_a_token()

	def tearDown(self):
		frappe.cache().delete_value(nvoip.TOKEN_CACHE_KEY)

	def test_history_rows_are_read_as_incoming_calls(self):
		row = {
			"date": "12/01/2026 14:30:34",
			"type": "inbound",
			"origin": "554833328530",
			"destination": "558400000000",
			"duration": "00:00:17",
			"status": "Completada",
			"audio": "https://x/a.mp3",
		}
		responses = [
			MagicMock(status_code=200, json=lambda: [row]),
			MagicMock(status_code=200, json=lambda: []),
		]
		with patch.object(nvoip.requests, "request", side_effect=responses):
			calls = nvoip.poll_inbound_history(nvoip_settings())

		self.assertEqual(len(calls), 1)
		call = calls[0]
		self.assertEqual(
			(call["type"], call["number"], call["status"], call["duration"], call["recording_url"]),
			("Incoming", "554833328530", "Completed", 17, "https://x/a.mp3"),
		)
		self.assertTrue(call["id"].startswith("nvoip-"))

	def test_a_dict_wrapped_listing_is_also_read(self):
		row = {
			"date": "12/01/2026 14:30:34",
			"type": "inbound",
			"origin": "1",
			"destination": "2",
			"duration": "00:00:05",
		}
		wrapped = MagicMock(status_code=200, json=lambda: {"data": [row]})
		empty = MagicMock(status_code=200, json=lambda: {"data": []})
		with patch.object(nvoip.requests, "request", side_effect=[wrapped, empty]):
			calls = nvoip.poll_inbound_history(nvoip_settings())
		self.assertEqual(len(calls), 1)

	def test_the_same_row_makes_the_same_id_twice(self):
		row = {
			"date": "12/01/2026 14:30:34",
			"type": "inbound",
			"origin": "1",
			"destination": "2",
			"duration": "00:00:05",
		}
		self.assertEqual(nvoip.history_row_id(row), nvoip.history_row_id(dict(row)))

	def test_a_different_row_makes_a_different_id(self):
		row1 = {
			"date": "12/01/2026 14:30:34",
			"type": "inbound",
			"origin": "1",
			"destination": "2",
			"duration": "00:00:05",
		}
		row2 = {**row1, "duration": "00:00:06"}
		self.assertNotEqual(nvoip.history_row_id(row1), nvoip.history_row_id(row2))

	def test_an_unrecognized_status_is_read_as_failed(self):
		row = {
			"date": "12/01/2026 14:30:34",
			"type": "inbound",
			"origin": "1",
			"destination": "2",
			"duration": "00:00:01",
			"status": "Alguma coisa nova",
		}
		self.assertEqual(nvoip.parse_history_row(row)["status"], "Failed")

	def test_a_failing_history_request_is_logged_and_skipped(self):
		with patch.object(nvoip.requests, "request", return_value=MagicMock(status_code=500, text="")):
			self.assertEqual(nvoip.poll_inbound_history(nvoip_settings()), [])
