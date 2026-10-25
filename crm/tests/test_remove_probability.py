# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import json

import frappe

from crm.fcrm.doctype.crm_dashboard.crm_dashboard import create_default_manager_dashboard
from crm.fcrm.doctype.crm_pipeline.fields import catalog_fieldnames, default_pipeline_fields
from crm.patches.credhub.remove_probability import execute as remove_probability
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests import default_test_pipeline


class TestRemoveProbability(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_not_offered_for_pipelines(self):
		self.assertNotIn("probability", default_pipeline_fields())
		self.assertNotIn("probability", catalog_fieldnames())

	def test_card_no_longer_copies_stage_probability(self):
		card = frappe.get_doc(
			{"doctype": "CRM Deal", "pipeline": default_test_pipeline(), "status": "Negotiation"}
		).insert(ignore_permissions=True)
		self.assertFalse(card.probability)

	def test_default_dashboard_has_no_forecast(self):
		self.assertNotIn("forecasted_revenue", create_default_manager_dashboard(force=True))

	def test_patch_strips_saved_settings(self):
		layout = frappe.get_doc(
			{
				"doctype": "CRM Fields Layout",
				"dt": "CRM Deal",
				"type": "Data Fields",
				"layout": json.dumps(
					[{"columns": [{"fields": ["organization", "probability", {"fieldname": "probability"}]}]}]
				),
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)
		view = frappe.get_doc(
			{
				"doctype": "CRM View Settings",
				"dt": "CRM Deal",
				"label": "P",
				"type": "list",
				"columns": json.dumps([{"key": "probability"}, {"key": "status"}]),
				"rows": json.dumps(["name", "probability"]),
				"filters": json.dumps({"probability": [">", 10], "status": "Won"}),
			}
		).insert(ignore_permissions=True)
		pipeline = frappe.get_doc("CRM Pipeline", default_test_pipeline())
		frappe.db.sql(
			"""insert into `tabCRM Pipeline Field` (name, parent, parenttype, parentfield, fieldname, idx)
			values ('test-prob', %s, 'CRM Pipeline', 'fields', 'probability', 99)""",
			pipeline.name,
		)

		remove_probability()

		self.assertNotIn("probability", frappe.db.get_value("CRM Fields Layout", layout.name, "layout"))
		saved = frappe.db.get_value(
			"CRM View Settings", view.name, ["columns", "rows", "filters"], as_dict=True
		)
		self.assertEqual(json.loads(saved.columns), [{"key": "status"}])
		self.assertEqual(json.loads(saved.rows), ["name"])
		self.assertEqual(json.loads(saved.filters), {"status": "Won"})
		self.assertFalse(frappe.db.exists("CRM Pipeline Field", {"fieldname": "probability"}))
		self.assertNotIn(
			"forecasted_revenue", frappe.db.get_value("CRM Dashboard", "Manager Dashboard", "layout") or ""
		)
