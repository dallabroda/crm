# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Native fields reviewed by the owner on 28/10/2026: repeated or unused fields leave the forms of organizations
and contacts, and a contact has one name field (the full name)."""

import frappe

from crm.fcrm.doctype.crm_pipeline import form_schema
from crm.tests import CRMTestCase as FrappeTestCase


class TestNativeFields(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def catalog(self, doctype):
		return {f["fieldname"] for f in form_schema.form_catalog(doctype)}

	def test_repeated_and_unused_fields_leave_the_forms(self):
		organization = self.catalog("CRM Organization")
		for fieldname in ("territory", "legal_name", "trade_name", "employee_count", "employee_range"):
			self.assertNotIn(fieldname, organization)
		self.assertIn("no_of_employees", organization)
		contact = self.catalog("Contact")
		for fieldname in ("salutation", "gender", "address", "middle_name", "last_name", "company_name"):
			self.assertNotIn(fieldname, contact)
		self.assertIn("phone", contact)
		self.assertIn("first_name", contact)

	def test_a_contact_keeps_one_full_name(self):
		contact = frappe.get_doc(
			{"doctype": "Contact", "first_name": "Ana", "middle_name": "Maria", "last_name": "Souza"}
		).insert()
		self.assertEqual((contact.first_name, contact.middle_name, contact.last_name), ("Ana Maria Souza", None, None))
		self.assertEqual(contact.full_name, "Ana Maria Souza")
		contact.last_name = "Lima"
		contact.save()
		self.assertEqual(contact.first_name, "Ana Maria Souza Lima")
