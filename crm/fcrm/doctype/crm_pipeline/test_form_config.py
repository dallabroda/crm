# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.api.forms import create_field, get_form_schema, save_form_config
from crm.api.pipeline import save_pipeline
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"


class TestFormConfig(FrappeTestCase):
	"""Dynamic forms, phase 2 (credtech#180): saving the card form of a funnel, per stage or for all."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.created = []

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for fieldname in cls.created:
			name = frappe.db.get_value("Custom Field", {"dt": "CRM Deal", "fieldname": fieldname})
			if name:
				frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
		# creating a field commits (table change): the funnels saved before it stayed
		for name in frappe.get_all("CRM Pipeline", {"pipeline_name": "Form config test"}, pluck="name"):
			frappe.db.delete("CRM Deal Status", {"pipeline": name})
			frappe.delete_doc("CRM Pipeline", name, ignore_permissions=True, force=True)
		frappe.db.commit()  # nosemgrep: persist cleanup of committed custom fields and funnels
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Form config test",
				"stages": [{"deal_status": "Lead"}, {"deal_status": "Proposal"}],
				"fields": ["deal_value", "next_step", "source"],
			}
		)
		self.name = self.pipeline["name"]
		self.lead, self.proposal = (s["name"] for s in self.pipeline["stages"])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _by_name(self, stage=None):
		return {f["fieldname"]: f for f in get_form_schema("CRM Deal", self.name, stage)["fields"]}

	def _save(self, fields, stage=None):
		return save_form_config("CRM Deal", fields, self.name, stage)

	def test_order_and_list_become_the_funnel_s(self):
		schema = self._save([{"fieldname": "source"}, {"fieldname": "deal_value"}])
		names = [f["fieldname"] for f in schema["fields"] if not f["locked"]]
		self.assertEqual(names, ["source", "deal_value"])

	def test_one_stage_changes_only_that_stage(self):
		self._save(
			[
				{"fieldname": "deal_value", "visible": 1, "required": 1, "read_only": 0},
				{"fieldname": "next_step"},
				{"fieldname": "source"},
			],
			self.proposal,
		)
		self.assertEqual(self._by_name(self.proposal)["deal_value"]["required"], 1)
		self.assertEqual(self._by_name(self.lead)["deal_value"]["required"], 0)
		self.assertTrue(self._by_name()["deal_value"]["varies"]["required"])

	def test_all_stages_is_a_batch_edit(self):
		self._save([{"fieldname": "next_step", "visible": 0}], self.lead)
		# None = left as it is in each stage; a value = the same in every stage
		self._save(
			[
				{"fieldname": "next_step", "visible": None, "required": 0, "read_only": 1},
				{"fieldname": "deal_value", "visible": 1, "required": 1, "read_only": 0},
				{"fieldname": "source"},
			]
		)
		lead, proposal = self._by_name(self.lead), self._by_name(self.proposal)
		self.assertEqual((lead["deal_value"]["required"], proposal["deal_value"]["required"]), (1, 1))
		# read only implies visible: the stage that hid it shows it again
		self.assertEqual((lead["next_step"]["visible"], proposal["next_step"]["visible"]), (1, 1))

	def test_hidden_field_is_neither_required_nor_read_only(self):
		self._save([{"fieldname": "deal_value", "visible": 0, "required": 1}], self.lead)
		# required wins: a required field must be visible
		self.assertEqual(self._by_name(self.lead)["deal_value"]["visible"], 1)
		self._save([{"fieldname": "deal_value", "visible": 0, "required": 0, "read_only": 1}], self.lead)
		self.assertEqual(self._by_name(self.lead)["deal_value"]["visible"], 1)
		self._save([{"fieldname": "deal_value", "visible": 0}], self.lead)
		field = self._by_name(self.lead)["deal_value"]
		self.assertEqual((field["visible"], field["required"], field["read_only_rule"]), (0, 0, 0))

	def test_locked_fields_are_ignored(self):
		schema = self._save([{"fieldname": "status", "visible": 0}, {"fieldname": "deal_value"}])
		status = next(f for f in schema["fields"] if f["fieldname"] == "status")
		self.assertEqual((status["visible"], status["locked"]), (1, 1))

	def test_stage_must_belong_to_the_funnel(self):
		other = save_pipeline({"pipeline_name": "Form config test", "stages": [{"deal_status": "Other"}]})
		with self.assertRaises(frappe.ValidationError):
			self._save([{"fieldname": "deal_value"}], other["stages"][0]["name"])

	def test_repeated_field_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self._save([{"fieldname": "deal_value"}, {"fieldname": "deal_value"}])

	def test_only_funnel_owners_save(self):
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			self._save([{"fieldname": "deal_value"}])

	def test_new_field_goes_to_the_chosen_funnels_and_stages(self):
		field = create_field(
			"Garantia config test",
			"Data",
			placement=[{"pipeline": self.name, "stages": [self.proposal]}],
			required=1,
		)
		fieldname = field["fieldname"]
		self.created.append(fieldname)
		lead, proposal = self._by_name(self.lead), self._by_name(self.proposal)
		self.assertEqual(lead[fieldname]["visible"], 0)
		self.assertEqual((proposal[fieldname]["visible"], proposal[fieldname]["required"]), (1, 1))
		names = [f["fieldname"] for f in get_form_schema("CRM Deal", self.name)["fields"]]
		self.assertEqual(names[-1], fieldname)

	def test_new_field_with_unknown_stage_is_not_created(self):
		with self.assertRaises(frappe.ValidationError):
			create_field("Nunca config test", "Data", placement=[{"pipeline": self.name, "stages": ["nope"]}])
		self.assertFalse(frappe.db.exists("Custom Field", {"dt": "CRM Deal", "label": "Nunca config test"}))
