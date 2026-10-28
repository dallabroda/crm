# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Dynamic forms phase 5 (credtech#196): fields of the card's organization, second organization and primary
contact, shown and required stage by stage, checked when the card moves and filled in at that moment."""

import frappe

from crm.api.forms import get_form_schema, save_form_config
from crm.api.pipeline import get_missing_fields, get_pipeline_config, move_card, save_pipeline
from crm.fcrm.doctype.crm_pipeline import fields as catalog
from crm.fcrm.doctype.crm_pipeline.fields import MissingRequiredFieldsError
from crm.tests import CRMTestCase as FrappeTestCase

ORG = "CRM Organization"


class TestFormBlocks(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Blocks test",
				"stages": [{"deal_status": "Lead in"}, {"deal_status": "Proposal"}],
				"second_organization_label": "Sacado",
			}
		)
		self.first, self.proposal = (s["name"] for s in self.pipeline["stages"])
		# the proposal stage asks for the organization's website and the contact's mobile
		save_form_config(
			"CRM Deal",
			[{"fieldname": "website", "visible": 1, "required": 0}],
			self.pipeline["name"],
			block=catalog.ORGANIZATION,
		)
		save_form_config(
			"CRM Deal",
			[{"fieldname": "website", "visible": 1, "required": 1}],
			self.pipeline["name"],
			stage=self.proposal,
			block=catalog.ORGANIZATION,
		)
		# the contact's mobile is in the funnel but only shows (and is required) in the proposal stage
		save_form_config(
			"CRM Deal",
			[{"fieldname": "mobile_no", "visible": 0}],
			self.pipeline["name"],
			block=catalog.CONTACT,
		)
		save_form_config(
			"CRM Deal",
			[{"fieldname": "mobile_no", "visible": 1, "required": 1}],
			self.pipeline["name"],
			stage=self.proposal,
			block=catalog.CONTACT,
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def card(self, organization=True, contact=True):
		values = {"doctype": "CRM Deal", "pipeline": self.pipeline["name"], "status": self.first}
		if organization:
			values["organization"] = frappe.get_doc({"doctype": ORG, "organization_name": "Blocks Org"}).insert().name
		if contact:
			person = frappe.get_doc({"doctype": "Contact", "first_name": "Bia"}).insert().name
			values["contacts"] = [{"contact": person, "is_primary": 1}]
		return frappe.get_doc(values).insert()

	def test_the_stage_shows_and_requires_fields_of_the_linked_records(self):
		schema = get_form_schema("CRM Deal", self.pipeline["name"], self.proposal, catalog.ORGANIZATION)
		self.assertEqual((schema["block"], schema["block_doctype"]), (catalog.ORGANIZATION, ORG))
		self.assertEqual([(f["fieldname"], f["required"]) for f in schema["fields"]], [("website", 1)])
		self.assertIn("Sacado", [b["label"] for b in schema["blocks"]])
		first = get_form_schema("CRM Deal", self.pipeline["name"], self.first, catalog.ORGANIZATION)
		self.assertEqual([(f["fieldname"], f["required"]) for f in first["fields"]], [("website", 0)])

	def test_moving_needs_the_linked_records_fields(self):
		card = self.card()
		missing = get_missing_fields(card.name, self.proposal)
		self.assertEqual(
			sorted((m["block"], m["fieldname"]) for m in missing),
			[(catalog.CONTACT, "mobile_no"), (catalog.ORGANIZATION, "website")],
		)
		self.assertEqual(next(m for m in missing if m["block"] == catalog.ORGANIZATION)["docname"], card.organization)
		with self.assertRaises(MissingRequiredFieldsError):
			move_card(card.name, self.proposal)

	def test_values_by_block_fill_the_linked_records_while_moving(self):
		card = self.card()
		move_card(
			card.name,
			self.proposal,
			{"organization": {"website": "https://blocks.example"}, "contact": {"mobile_no": "48999990000"}},
		)
		self.assertEqual(frappe.db.get_value("CRM Deal", card.name, "status"), self.proposal)
		self.assertEqual(frappe.db.get_value(ORG, card.organization, "website"), "https://blocks.example")
		self.assertEqual(frappe.db.get_value("Contact", card.contacts[0].contact, "mobile_no"), "48999990000")

	def test_moving_is_not_a_way_to_edit_other_fields(self):
		card = self.card()
		with self.assertRaises(frappe.PermissionError):
			move_card(
				card.name,
				self.proposal,
				{
					"organization": {"website": "https://blocks.example", "organization_name": "Renamed"},
					"contact": {"mobile_no": "48999990000"},
				},
			)
		self.assertEqual(frappe.db.get_value(ORG, card.organization, "organization_name"), "Blocks Org")

	def test_a_block_without_a_record_is_skipped(self):
		card = self.card(organization=False, contact=False)
		self.assertEqual(get_missing_fields(card.name, self.proposal), [])
		move_card(card.name, self.proposal)

	def test_saving_one_block_keeps_the_others(self):
		save_form_config("CRM Deal", [{"fieldname": "next_step", "visible": 1}], self.pipeline["name"])
		fields = [(f["block"], f["fieldname"]) for f in get_pipeline_config(self.pipeline["name"])["fields"]]
		self.assertIn((catalog.ORGANIZATION, "website"), fields)
		self.assertIn((catalog.CONTACT, "mobile_no"), fields)
		self.assertIn((catalog.CARD, "next_step"), fields)

	def test_old_style_field_list_keeps_the_blocks(self):
		save_pipeline({"name": self.pipeline["name"], "fields": ["next_step"]})
		fields = [(f["block"], f["fieldname"]) for f in get_pipeline_config(self.pipeline["name"])["fields"]]
		self.assertEqual(fields[0], (catalog.CARD, "next_step"))
		self.assertIn((catalog.ORGANIZATION, "website"), fields)

	def test_removing_every_field_of_a_block(self):
		save_form_config("CRM Deal", [], self.pipeline["name"], block=catalog.CONTACT)
		fields = [(f["block"], f["fieldname"]) for f in get_pipeline_config(self.pipeline["name"])["fields"]]
		self.assertNotIn((catalog.CONTACT, "mobile_no"), fields)
		self.assertIn((catalog.ORGANIZATION, "website"), fields)

	def test_linked_record_fields_are_never_read_only_on_the_card(self):
		save_form_config(
			"CRM Deal",
			[{"fieldname": "website", "visible": 1, "read_only": 1}],
			self.pipeline["name"],
			block=catalog.ORGANIZATION,
		)
		rules = [r for r in get_pipeline_config(self.pipeline["name"])["field_rules"] if r["block"] == catalog.ORGANIZATION]
		self.assertTrue(rules)
		self.assertFalse(any(r["read_only"] for r in rules))

	def test_only_fields_of_that_form(self):
		with self.assertRaises(frappe.ValidationError):
			save_form_config(
				"CRM Deal", [{"fieldname": "deal_value", "visible": 1}], self.pipeline["name"], block=catalog.ORGANIZATION
			)
		with self.assertRaises(frappe.ValidationError):
			save_form_config(
				"CRM Deal",
				[{"fieldname": "organization_name", "visible": 1}],
				self.pipeline["name"],
				block=catalog.ORGANIZATION,
			)

	def test_the_card_shows_the_blocks_of_its_stage(self):
		from crm.api.forms import get_card_blocks

		card = self.card()
		blocks = {b["block"]: b for b in get_card_blocks(card.name)}
		# first stage: the organization's website shows (not required); the contact's mobile only in proposal
		self.assertEqual(list(blocks), [catalog.ORGANIZATION])
		self.assertEqual(blocks[catalog.ORGANIZATION]["docname"], card.organization)
		self.assertEqual([f["fieldname"] for f in blocks[catalog.ORGANIZATION]["fields"]], ["website"])
		frappe.db.set_value(ORG, card.organization, "website", "https://x.example")
		frappe.db.set_value(
			"Contact", card.contacts[0].contact, "mobile_no", "48999990000"
		)
		card.reload()
		card.status = self.proposal
		card.save()
		blocks = {b["block"]: b for b in get_card_blocks(card.name)}
		self.assertEqual(sorted(blocks), [catalog.CONTACT, catalog.ORGANIZATION])
		self.assertEqual(blocks[catalog.CONTACT]["fields"][0]["reqd"], 1)
