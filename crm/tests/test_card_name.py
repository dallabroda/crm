# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""The card's name (credtech#182): locked, always filled, shown as the card's title."""

import frappe

from crm.api.forms import get_form_schema
from crm.api.pipeline import save_pipeline
from crm.tests import CRMTestCase as FrappeTestCase


class TestCardName(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline({"pipeline_name": "Card name test", "stages": [{"deal_status": "New"}]})

	def tearDown(self):
		frappe.db.rollback()

	def card(self, **values):
		return frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"pipeline": self.pipeline["name"],
				"status": self.pipeline["stages"][0]["name"],
				**values,
			}
		).insert()

	def test_typed_name_is_kept(self):
		self.assertEqual(self.card(deal_name="  Home equity Ana  ").deal_name, "Home equity Ana")

	def test_empty_name_takes_the_organization(self):
		org = frappe.get_doc({"doctype": "CRM Organization", "organization_name": "Acme Nome"}).insert().name
		self.assertEqual(self.card(organization=org).deal_name, "Acme Nome")

	def test_without_organization_it_takes_the_contact_or_the_person(self):
		contact = frappe.get_doc({"doctype": "Contact", "first_name": "Bia Nome Card"}).insert().name
		self.assertEqual(self.card(contacts=[{"contact": contact, "is_primary": 1}]).deal_name, "Bia Nome Card")
		self.assertEqual(self.card(first_name="Caio", last_name="Lima").deal_name, "Caio Lima")

	def test_clearing_the_name_fills_it_again(self):
		org = frappe.get_doc({"doctype": "CRM Organization", "organization_name": "Acme Limpa"}).insert().name
		card = self.card(organization=org, deal_name="Nome digitado")
		card.deal_name = ""
		card.save()
		self.assertEqual(card.deal_name, "Acme Limpa")

	def test_name_is_the_title_and_locked_in_the_form(self):
		self.assertEqual(frappe.get_meta("CRM Deal").title_field, "deal_name")
		fields = get_form_schema("CRM Deal", self.pipeline["name"], self.pipeline["stages"][0]["name"])["fields"]
		name = next(f for f in fields if f["fieldname"] == "deal_name")
		self.assertEqual((name["locked"], name["required"]), (1, 1))
