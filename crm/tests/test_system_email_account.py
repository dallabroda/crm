from unittest.mock import patch

import frappe
from frappe.client import set_value

from crm.api.email_accounts import before_rename, get_system_email_accounts
from crm.tests import CRMTestCase as FrappeTestCase

SYSTEM = "HubTech System Test"
MANAGER = "crm.manager@example.com"


class TestSystemEmailAccount(FrappeTestCase):
	"""credtech#191: the account that sends the platform's emails cannot be changed by the company."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.hook = patch("crm.api.email_accounts.system_email_accounts", return_value=[SYSTEM])
		self.hook.start()
		# inserted without the controller, which would test a real mail server
		doc = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": SYSTEM,
				"email_id": "no-reply@system.example.test",
				"enable_outgoing": 1,
				"smtp_server": "smtp.system.example.test",
				"awaiting_password": 1,
			}
		)
		doc.name = SYSTEM
		doc.db_insert()

	def tearDown(self):
		self.hook.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_the_screen_is_told_which_accounts_to_leave_out(self):
		frappe.set_user(MANAGER)
		self.assertEqual(get_system_email_accounts(), [SYSTEM])

	def test_company_users_cannot_change_it(self):
		frappe.set_user(MANAGER)
		doc = frappe.get_doc("Email Account", SYSTEM)
		doc.enable_incoming = 1
		with self.assertRaises(frappe.PermissionError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			set_value("Email Account", SYSTEM, "email_id", "x@y.example.test")

	def test_company_users_cannot_delete_or_rename_it(self):
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("Email Account", SYSTEM, ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			before_rename(frappe.get_doc("Email Account", SYSTEM), old=SYSTEM, new="Mine now")
		hooks = frappe.get_hooks("doc_events")["Email Account"]
		self.assertIn("crm.api.email_accounts.before_rename", hooks["before_rename"])
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("Email Account", SYSTEM))

	def test_setup_scripts_still_manage_it(self):
		# site_setup runs as Administrator
		doc = frappe.get_doc("Email Account", SYSTEM)
		doc.email_id = "no-reply2@system.example.test"
		doc.save(ignore_permissions=True)
		self.assertEqual(
			frappe.db.get_value("Email Account", SYSTEM, "email_id"), "no-reply2@system.example.test"
		)

	def test_company_account_is_never_the_default_for_sending(self):
		company = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Company Inbox Test",
				"email_id": "vendas@company.example.test",
				"enable_outgoing": 1,
				"default_outgoing": 1,
				"smtp_server": "smtp.company.example.test",
				"awaiting_password": 1,
			}
		)
		frappe.set_user(MANAGER)
		company.insert(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Email Account", company.name, "default_outgoing"), 0)
		company.default_outgoing = 1
		company.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Email Account", company.name, "default_outgoing"), 0)
