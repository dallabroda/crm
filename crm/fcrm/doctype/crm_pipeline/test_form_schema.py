# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.api.forms import get_form_schema
from crm.api.pipeline import create_field, disable_field, save_pipeline
from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.tests import CRMTestCase as FrappeTestCase


class TestFormSchema(FrappeTestCase):
	"""Dynamic forms, phase 1 (credtech#179): the card form follows the pipeline order and the stage rules,
	and a created field shows up without editing any layout."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Custom fields change the table (implicit commit): created once and removed at the end
		cls.income = create_field("Renda schema test", "Currency")["fieldname"]
		cls.old = create_field("Antigo schema test", "Data")["fieldname"]
		frappe.db.commit()  # nosemgrep: custom fields are DDL and must persist for the class

	@classmethod
	def tearDownClass(cls):
		for doctype, fieldname in (("CRM Deal", cls.income), ("CRM Deal", cls.old)):
			name = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname})
			if name:
				frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
		frappe.db.commit()  # nosemgrep: persist cleanup of committed custom fields
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Schema test",
				"stages": [{"deal_status": "Lead"}, {"deal_status": "Proposal"}],
				# order of the form: the created field first, then the standard ones
				"fields": [self.income, "next_step", "deal_value", self.old],
			}
		)
		self.lead, self.proposal = (s["name"] for s in self.pipeline["stages"])
		save_pipeline(
			{
				"name": self.pipeline["name"],
				"field_rules": [
					{"stage": self.proposal, "fieldname": self.income, "visible": 1, "required": 1},
					{"stage": self.lead, "fieldname": "next_step", "visible": 0, "required": 0},
				],
			}
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _schema(self, stage=None):
		return get_form_schema("CRM Deal", self.pipeline["name"], stage)["fields"]

	def test_order_follows_the_pipeline_after_the_locked_fields(self):
		names = [f["fieldname"] for f in self._schema(self.lead)]
		locked = list(field_catalog.LOCKED_FIELDS)
		self.assertEqual(names[: len(locked)], locked)
		self.assertEqual(names[len(locked) :], [self.income, "next_step", "deal_value", self.old])

	def test_created_field_is_in_the_form_with_the_stage_rules(self):
		by_name = {f["fieldname"]: f for f in self._schema(self.proposal)}
		income = by_name[self.income]
		self.assertEqual((income["visible"], income["required"], income["reqd"]), (1, 1, 1))
		self.assertEqual(income["is_created"], 1)
		self.assertEqual(income["fieldtype"], "Currency")
		self.assertFalse(by_name["next_step"]["required"])

	def test_hidden_in_one_stage_only(self):
		lead = {f["fieldname"]: f for f in self._schema(self.lead)}
		proposal = {f["fieldname"]: f for f in self._schema(self.proposal)}
		self.assertEqual(lead["next_step"]["visible"], 0)
		self.assertEqual(proposal["next_step"]["visible"], 1)

	def test_all_stages_say_when_stages_differ(self):
		all_stages = {f["fieldname"]: f for f in self._schema()}
		self.assertIsNone(all_stages["next_step"]["visible"])
		self.assertTrue(all_stages["next_step"]["varies"]["visible"])
		self.assertEqual(all_stages["deal_value"]["visible"], 1)
		self.assertFalse(all_stages["deal_value"]["varies"]["visible"])

	def test_disabled_created_field_leaves_the_form(self):
		disable_field(self.old)
		names = [f["fieldname"] for f in self._schema(self.lead)]
		self.assertNotIn(self.old, names)
		# disabling saves the Custom Field (and commits with the table change): turn it back on for the others
		frappe.db.set_value("Custom Field", {"dt": "CRM Deal", "fieldname": self.old}, "hidden", 0)
		# the same implicit commit kept this test's pipeline: remove it too
		pipeline = self.pipeline["name"]
		frappe.db.delete("CRM Deal Status", {"pipeline": pipeline})
		frappe.delete_doc("CRM Pipeline", pipeline, ignore_permissions=True, force=True)
		frappe.db.commit()  # nosemgrep: undo the committed changes for the next tests
		frappe.clear_cache(doctype="CRM Deal")

	def test_contacts_and_companies_have_a_global_form_with_the_name_locked(self):
		contact = get_form_schema("Contact")["fields"]
		self.assertEqual(contact[0]["fieldname"], "first_name")
		self.assertEqual(contact[0]["locked"], 1)
		company = get_form_schema("CRM Organization")["fields"]
		self.assertEqual(company[0]["fieldname"], "organization_name")

	def test_card_form_needs_a_pipeline(self):
		with self.assertRaises(frappe.ValidationError):
			get_form_schema("CRM Deal")

	def test_only_cards_contacts_and_companies(self):
		with self.assertRaises(frappe.ValidationError):
			get_form_schema("CRM Lead")
