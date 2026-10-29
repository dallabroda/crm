from unittest.mock import MagicMock, patch

import frappe
from frappe.utils.password import delete_all_passwords_for

from crm.fcrm.doctype.crm_wavix_settings import crm_wavix_settings as wavix_settings
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"
API_KEY = "key-for-tests"


def wavix_answers(status=200):
	return MagicMock(status_code=status, text="{}")


class TestWavixSettings(FrappeTestCase):
	"""The webhook registration at Wavix is mocked: it was not run against the real API (credtech#271)."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("CRM Wavix Settings", "enabled", 0)
		delete_all_passwords_for("CRM Wavix Settings", "CRM Wavix Settings")
		self.patch = patch.object(wavix_settings.requests, "post", return_value=wavix_answers())
		self.wavix = self.patch.start()

	def tearDown(self):
		self.patch.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def enable(self, api_key=API_KEY):
		settings = frappe.get_single("CRM Wavix Settings")
		settings.update({"enabled": 1, "api_key": api_key})
		settings.save()
		return frappe.get_single("CRM Wavix Settings")

	def test_enabling_needs_the_key(self):
		with self.assertRaises(frappe.ValidationError):
			self.enable(api_key="")
		self.wavix.assert_not_called()

	def test_enabling_generates_the_secret_and_registers_the_webhook(self):
		settings = self.enable()
		secret = settings.get_password("webhook_secret")
		self.assertEqual(len(secret), 40)

		self.wavix.assert_called_once()
		args, kwargs = self.wavix.call_args
		self.assertEqual(args[0], "https://api.wavix.com/v1/calls/webhooks")
		self.assertEqual(kwargs["headers"], {"Authorization": f"Bearer {API_KEY}"})
		body = kwargs["json"]
		self.assertEqual(body["event_type"], "post-call")
		self.assertTrue(body["url"].endswith(f"/api/method/crm.integrations.voip.webhook.wavix?key={secret}"))

	def test_key_and_secret_never_come_back(self):
		self.enable()
		doc = frappe.get_doc("CRM Wavix Settings").as_dict()
		self.assertNotIn(API_KEY, str(doc))
		self.assertTrue(set(doc.api_key) == {"*"})

	def test_saving_without_changes_does_not_register_again(self):
		settings = self.enable()
		self.wavix.reset_mock()
		settings.save()
		self.wavix.assert_not_called()

	def test_new_key_registers_again(self):
		self.enable()
		self.wavix.reset_mock()
		self.enable(api_key="another-key")
		self.assertEqual(self.wavix.call_args.kwargs["headers"], {"Authorization": "Bearer another-key"})

	def test_new_key_of_the_same_length_registers_again(self):
		self.enable()
		self.wavix.reset_mock()
		same_length = "x" * len(API_KEY)
		self.enable(api_key=same_length)
		self.wavix.assert_called_once()

	def test_refused_key_stops_the_save(self):
		self.wavix.return_value = wavix_answers(401)
		with self.assertRaises(frappe.ValidationError):
			self.enable()

	def test_unreachable_wavix_stops_the_save(self):
		self.wavix.side_effect = wavix_settings.requests.ConnectionError
		with self.assertRaises(frappe.ValidationError):
			self.enable()

	def test_regenerate_secret_changes_the_url_and_registers_again(self):
		settings = self.enable()
		old = settings.get_webhook_url()
		self.wavix.reset_mock()
		settings.regenerate_webhook_secret()
		new = frappe.get_single("CRM Wavix Settings").get_webhook_url()
		self.assertNotEqual(old, new)
		self.assertEqual(self.wavix.call_args.kwargs["json"]["url"], new)

	def test_salesperson_sees_neither_key_nor_secret(self):
		settings = self.enable()
		self.assertFalse(frappe.has_permission("CRM Wavix Settings", "read", user=SALES_USER))
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			settings.get_webhook_url()
		with self.assertRaises(frappe.PermissionError):
			settings.regenerate_webhook_secret()
