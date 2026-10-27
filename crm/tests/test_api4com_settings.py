from unittest.mock import MagicMock, patch

import frappe

from crm.fcrm.doctype.crm_api4com_settings import crm_api4com_settings as api4com_settings
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"
TOKEN = "token-for-tests"


def api4com_answers(status=200):
	return MagicMock(status_code=status, text="{}")


class TestAPI4ComSettings(FrappeTestCase):
	"""The webhook registration at API4Com is mocked: it was not run against the real API (credtech#100)."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.patch = patch.object(api4com_settings.requests, "patch", return_value=api4com_answers())
		self.api4com = self.patch.start()

	def tearDown(self):
		self.patch.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def enable(self, token=TOKEN):
		settings = frappe.get_single("CRM API4Com Settings")
		settings.update({"enabled": 1, "api_token": token})
		settings.save()
		return frappe.get_single("CRM API4Com Settings")

	def test_enabling_needs_the_token(self):
		with self.assertRaises(frappe.ValidationError):
			self.enable(token="")
		self.api4com.assert_not_called()

	def test_enabling_generates_the_secret_and_registers_the_webhook(self):
		settings = self.enable()
		secret = settings.get_password("webhook_secret")
		self.assertEqual(len(secret), 40)

		self.api4com.assert_called_once()
		args, kwargs = self.api4com.call_args
		self.assertEqual(args[0], "https://api.api4com.com/api/v1/integrations")
		# API4Com takes the raw token, without "Bearer"
		self.assertEqual(kwargs["headers"], {"Authorization": TOKEN})
		body = kwargs["json"]
		self.assertTrue(body["webhook"])
		self.assertEqual(body["metadata"]["webhookTypes"], ["channel-hangup"])
		self.assertEqual(body["metadata"]["webhookVersion"], "v1.4")
		self.assertTrue(
			body["metadata"]["webhookUrl"].endswith(
				f"/api/method/crm.integrations.voip.webhook.api4com?key={secret}"
			)
		)

	def test_token_and_secret_never_come_back(self):
		self.enable()
		doc = frappe.get_doc("CRM API4Com Settings").as_dict()
		self.assertNotIn(TOKEN, str(doc))
		self.assertTrue(set(doc.api_token) == {"*"})

	def test_saving_without_changes_does_not_register_again(self):
		settings = self.enable()
		self.api4com.reset_mock()
		settings.save()
		self.api4com.assert_not_called()

	def test_new_token_registers_again(self):
		self.enable()
		self.api4com.reset_mock()
		self.enable(token="another-token")
		self.assertEqual(self.api4com.call_args.kwargs["headers"], {"Authorization": "another-token"})

	def test_refused_token_stops_the_save(self):
		self.api4com.return_value = api4com_answers(401)
		with self.assertRaises(frappe.ValidationError):
			self.enable()

	def test_unreachable_api4com_stops_the_save(self):
		self.api4com.side_effect = api4com_settings.requests.ConnectionError
		with self.assertRaises(frappe.ValidationError):
			self.enable()

	def test_regenerate_secret_changes_the_url_and_registers_again(self):
		settings = self.enable()
		old = settings.get_webhook_url()
		self.api4com.reset_mock()
		settings.regenerate_webhook_secret()
		new = frappe.get_single("CRM API4Com Settings").get_webhook_url()
		self.assertNotEqual(old, new)
		self.assertEqual(self.api4com.call_args.kwargs["json"]["metadata"]["webhookUrl"], new)

	def test_salesperson_sees_neither_token_nor_secret(self):
		settings = self.enable()
		self.assertFalse(frappe.has_permission("CRM API4Com Settings", "read", user=SALES_USER))
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			settings.get_webhook_url()
		with self.assertRaises(frappe.PermissionError):
			settings.regenerate_webhook_secret()
		with self.assertRaises(frappe.PermissionError):
			api4com_settings.set_extension(SALES_USER, "2001")

	def test_extension_per_user(self):
		self.assertEqual(api4com_settings.set_extension(SALES_USER, " 2001 ")["extension"], "2001")
		self.assertEqual(frappe.db.get_value("CRM Telephony Agent", SALES_USER, "api4com_extension"), "2001")
		# the same user keeps it; another user can't take it
		api4com_settings.set_extension(SALES_USER, "2001")
		with self.assertRaises(frappe.ValidationError):
			api4com_settings.set_extension("Administrator", "2001")
		for wrong in ("12a", "1234567"):
			with self.assertRaises(frappe.ValidationError):
				api4com_settings.set_extension(SALES_USER, wrong)
		api4com_settings.set_extension(SALES_USER, "")
		self.assertIsNone(frappe.db.get_value("CRM Telephony Agent", SALES_USER, "api4com_extension"))
