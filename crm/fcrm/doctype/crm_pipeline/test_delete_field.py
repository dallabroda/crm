# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Deleting a created field for good, and enabling a disabled one again (credtech#232). Creating and dropping a column
commit on their own, so each test removes what it created."""

import frappe

from crm.api import forms
from crm.api.forms import save_form_config
from crm.api.pipeline import save_pipeline
from crm.fcrm.doctype.crm_pipeline import fields as catalog
from crm.tests import CRMTestCase as FrappeTestCase

DEAL = "CRM Deal"


class TestDeleteField(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fieldname = catalog.create_field("Apagar teste", "Data")["fieldname"]
		self.pipeline = save_pipeline(
			{"pipeline_name": "Delete field test", "stages": [{"deal_status": "Novo"}]}
		)
		stage = self.pipeline["stages"][0]["name"]
		save_form_config(DEAL, [{"fieldname": self.fieldname, "visible": 1}], self.pipeline["name"])
		save_form_config(
			DEAL,
			[{"fieldname": self.fieldname, "visible": 1, "required": 1}],
			self.pipeline["name"],
			stage=stage,
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		if frappe.db.exists("Custom Field", {"dt": DEAL, "fieldname": self.fieldname}):
			catalog.delete_field(self.fieldname, DEAL)
		frappe.db.delete("CRM Pipeline", {"pipeline_name": "Delete field test"})
		frappe.db.commit()

	def card_with_value(self):
		deal = frappe.get_doc(
			{"doctype": DEAL, "pipeline": self.pipeline["name"], "status": self.pipeline["stages"][0]["name"]}
		)
		deal.set(self.fieldname, "valor")
		deal.flags.ignore_mandatory = True
		return deal.insert()

	def test_usage_counts_the_records_with_a_value(self):
		self.card_with_value()
		self.assertEqual(catalog.field_usage(self.fieldname, DEAL)["records"], 1)

	def test_delete_removes_the_field_its_rules_its_column_and_frees_the_room(self):
		count = catalog.created_field_count(DEAL)
		view = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"label": "Delete field view",
				"dt": DEAL,
				"type": "list",
				"columns": frappe.as_json([{"key": "deal_name"}, {"key": self.fieldname}]),
				"rows": frappe.as_json(["name", self.fieldname]),
			}
		).insert(ignore_permissions=True)

		catalog.delete_field(self.fieldname, DEAL)

		self.assertFalse(frappe.db.exists("Custom Field", {"dt": DEAL, "fieldname": self.fieldname}))
		self.assertFalse(frappe.db.has_column(DEAL, self.fieldname))
		for child in ("CRM Pipeline Field", "CRM Pipeline Field Rule"):
			self.assertFalse(frappe.db.exists(child, {"fieldname": self.fieldname}))
		view.reload()
		self.assertEqual(frappe.parse_json(view.columns), [{"key": "deal_name"}])
		self.assertEqual(frappe.parse_json(view.rows), ["name"])
		self.assertEqual(catalog.created_field_count(DEAL), count - 1)
		self.assertNotIn(self.fieldname, {f["fieldname"] for f in catalog.get_catalog()})
		view.delete(ignore_permissions=True)

	def test_a_disabled_field_can_be_enabled_again(self):
		catalog.disable_field(self.fieldname, DEAL)
		self.assertTrue(catalog.enable_field(self.fieldname, DEAL)["disabled"] == 0)

	def test_standard_fields_and_other_users_are_refused(self):
		with self.assertRaises(frappe.ValidationError):
			catalog.delete_field("deal_value", DEAL)
		frappe.set_user("crm.user1@example.com")
		with self.assertRaises(frappe.PermissionError):
			forms.delete_field(self.fieldname, DEAL)
		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("Custom Field", {"dt": DEAL, "fieldname": self.fieldname}))

	def test_mentions_are_removed_from_nested_layouts(self):
		layout = [{"name": "tab", "sections": [{"columns": [{"fields": ["deal_name", self.fieldname]}]}]}]
		self.assertEqual(
			catalog._without_field(layout, self.fieldname),
			[{"name": "tab", "sections": [{"columns": [{"fields": ["deal_name"]}]}]}],
		)
