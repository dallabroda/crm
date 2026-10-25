# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import json

import frappe

from crm.fcrm.doctype.crm_deal.crm_deal import CRMDeal
from crm.patches.credhub.kanban_card_value import NEW, OLD
from crm.patches.credhub.kanban_card_value import execute as switch_kanban_fields
from crm.tests import CRMTestCase as FrappeTestCase


class TestKanbanCardValue(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_default_shows_card_value_and_owner(self):
		fields = json.loads(CRMDeal.default_kanban_settings()["kanban_fields"])
		self.assertEqual(fields[:2], ["deal_value", "deal_owner"])
		self.assertNotIn("annual_revenue", fields)

	def test_patch_switches_only_views_on_the_old_default(self):
		def view(fields):
			return (
				frappe.get_doc(
					{
						"doctype": "CRM View Settings",
						"dt": "CRM Deal",
						"type": "kanban",
						"label": "K",
						"kanban_fields": json.dumps(fields),
					}
				)
				.insert(ignore_permissions=True)
				.name
			)

		old, custom = view(OLD), view(["organization", "probability"])
		switch_kanban_fields()
		self.assertEqual(json.loads(frappe.db.get_value("CRM View Settings", old, "kanban_fields")), NEW)
		self.assertEqual(
			json.loads(frappe.db.get_value("CRM View Settings", custom, "kanban_fields")),
			["organization", "probability"],
		)
