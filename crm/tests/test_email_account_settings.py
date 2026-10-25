# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

from unittest.mock import patch

import frappe

from crm.api.settings import create_email_account
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline
from crm.patches.credhub.stop_email_append_to_lead import execute as stop_append_to_lead
from crm.tests import CRMTestCase as FrappeTestCase

EMAIL_ACCOUNT = "frappe.email.doctype.email_account.email_account.EmailAccount"


def account_data(**kwargs):
	return {
		"service": "GMail",
		"email_id": "cards@example.com",
		"email_account_name": "Cards test",
		"password": "x",
		"enable_incoming": 1,
		**kwargs,
	}


class TestEmailAccountSettings(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_creating_cards_needs_a_pipeline(self):
		with self.assertRaises(frappe.ValidationError):
			create_email_account(account_data(create_lead_from_incoming_email=1))

	@patch(f"{EMAIL_ACCOUNT}.validate")
	@patch(f"{EMAIL_ACCOUNT}.get_incoming_server")
	def test_card_settings_are_saved_without_append_to(self, _server, _validate):
		pipeline = get_default_pipeline()
		create_email_account(account_data(create_lead_from_incoming_email=1, crm_pipeline=pipeline))
		account = frappe.get_doc("Email Account", "Cards test")
		self.assertEqual(account.create_lead_from_incoming_email, 1)
		self.assertEqual(account.crm_pipeline, pipeline)
		self.assertFalse(account.append_to)
		self.assertFalse([f.append_to for f in account.imap_folder if f.append_to])

	def test_patch_stops_appending_emails_to_leads(self):
		account = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Old CRM account",
				"email_id": "old@example.com",
				"append_to": "CRM Lead",
				"imap_folder": [{"folder_name": "INBOX", "append_to": "CRM Lead"}],
			}
		)
		account.flags.ignore_mandatory = True
		account.flags.ignore_validate = True
		account.insert(ignore_permissions=True)
		stop_append_to_lead()
		account.reload()
		self.assertFalse(account.append_to)
		self.assertFalse(account.imap_folder[0].append_to)
