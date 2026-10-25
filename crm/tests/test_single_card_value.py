# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import json

import frappe

from crm.fcrm.doctype.crm_pipeline.fields import catalog_fieldnames
from crm.patches.credhub.single_card_value import execute as single_card_value
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests import default_test_pipeline


class TestSingleCardValue(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def card(self, **values):
		return frappe.get_doc({"doctype": "CRM Deal", "pipeline": default_test_pipeline(), **values})

	def test_typed_value_kept_without_products(self):
		card = self.card(deal_value=1500).insert(ignore_permissions=True)
		self.assertEqual(card.deal_value, 1500)

	def test_products_total_becomes_the_value(self):
		product = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": "TEST-SCV",
				"product_name": "Test",
				"standard_rate": 250,
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)
		card = self.card(deal_value=10)
		card.append("products", {"product_code": product.name, "product_name": "Test", "qty": 2, "rate": 250})
		card.insert(ignore_permissions=True)
		self.assertEqual(card.deal_value, 500)

	def test_expected_value_not_offered(self):
		self.assertNotIn("expected_deal_value", catalog_fieldnames())

	def test_patch_moves_values_and_strips_screens(self):
		only_expected = self.card().insert(ignore_permissions=True)
		both = self.card(deal_value=70).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Deal", only_expected.name, "expected_deal_value", 900)
		frappe.db.set_value("CRM Deal", both.name, "expected_deal_value", 40)
		view = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"dt": "CRM Deal",
				"label": "V",
				"type": "list",
				"columns": json.dumps([{"key": "expected_deal_value"}, {"key": "deal_value"}]),
			}
		).insert(ignore_permissions=True)

		single_card_value()

		self.assertEqual(frappe.db.get_value("CRM Deal", only_expected.name, "deal_value"), 900)
		self.assertEqual(frappe.db.get_value("CRM Deal", both.name, "deal_value"), 70)
		self.assertEqual(
			json.loads(frappe.db.get_value("CRM View Settings", view.name, "columns")),
			[{"key": "deal_value"}],
		)
		self.assertFalse(frappe.db.get_single_value("FCRM Settings", "auto_update_expected_deal_value"))
