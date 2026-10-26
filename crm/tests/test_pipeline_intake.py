# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import add as assign_add

from crm.api.form import _seed_hidden_fields
from crm.api.pipeline import save_pipeline
from crm.fcrm.doctype.crm_call_log.crm_call_log import create_lead_from_call_log
from crm.fcrm.doctype.crm_call_log.test_crm_call_log import create_test_call_log
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline
from crm.fcrm.doctype.crm_pipeline.fields import MissingRequiredFieldsError
from crm.lead_syncing.doctype.lead_sync_source.facebook import FacebookSyncSource
from crm.tests import CRMTestCase as FrappeTestCase

MEMBER = "crm.user1@example.com"
OUTSIDER = "intake-outsider@example.com"


class TestPipelineIntake(FrappeTestCase):
	"""Automatic entries arrive as a lead with the pipeline chosen in the integration and become a card."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("User", OUTSIDER):
			user = frappe.get_doc(
				{"doctype": "User", "email": OUTSIDER, "first_name": "Outsider", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
			user.add_roles("Sales User")
		frappe.db.commit()  # nosemgrep: fixture user must persist across committing hooks

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Intake",
				"stages": [{"deal_status": "New"}, {"deal_status": "Won", "type": "Won"}],
				"members": [{"user": MEMBER, "role": "Member"}],
			}
		)
		self.first_stage = self.pipeline["stages"][0]["name"]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for name in frappe.get_all("CRM Pipeline", {"pipeline_name": "Intake"}, pluck="name"):
			for card in frappe.get_all("CRM Deal", {"pipeline": name}, pluck="name"):
				frappe.db.delete("ToDo", {"reference_type": "CRM Deal", "reference_name": card})
				frappe.delete_doc("CRM Deal", card, force=True, ignore_permissions=True)
			frappe.delete_doc("CRM Pipeline", name, force=True, ignore_permissions=True)
		frappe.db.commit()  # nosemgrep: card inserts commit, so clean up explicitly

	def card_of(self, lead):
		return frappe.get_doc("CRM Deal", {"lead": lead})

	def make_lead(self, **kwargs):
		return frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Ana", "pipeline": self.pipeline["name"], **kwargs}
		).insert(ignore_permissions=True)

	def test_lead_with_pipeline_becomes_card(self):
		lead = self.make_lead(email="ana@example.com", lead_owner=MEMBER)
		card = self.card_of(lead.name)
		self.assertEqual(card.pipeline, self.pipeline["name"])
		self.assertEqual(card.status, self.first_stage)
		self.assertEqual(card.deal_owner, MEMBER)
		self.assertEqual(frappe.db.get_value("CRM Lead", lead.name, "converted"), 1)

	def test_entry_stage_required_fields_do_not_lose_the_entry(self):
		first = self.pipeline["stages"][0]["name"]
		save_pipeline(
			{
				"name": self.pipeline["name"],
				"fields": ["next_step"],
				"field_rules": [{"stage": first, "fieldname": "next_step", "required": 1}],
			}
		)
		lead = self.make_lead(email="required@example.com")
		self.assertEqual(self.card_of(lead.name).status, first)
		self.assertFalse(frappe.flags.get("crm_automatic_entry"))
		with self.assertRaises(MissingRequiredFieldsError):  # people creating cards still fill them
			frappe.get_doc(
				{"doctype": "CRM Deal", "pipeline": self.pipeline["name"], "deal_owner": "Administrator"}
			).insert()

	def test_owner_outside_pipeline_is_not_kept(self):
		# Someone outside the pipeline cannot own the card: the pipeline's distribution picks a member
		lead = self.make_lead(lead_owner=OUTSIDER)
		self.assertEqual(self.card_of(lead.name).deal_owner, MEMBER)

	def test_lead_without_pipeline_stays_a_lead(self):
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bia"}).insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("CRM Deal", {"lead": lead.name}))

	def test_facebook_sync_creates_card_in_source_pipeline(self):
		source = FacebookSyncSource("token", "form-1", pipeline=self.pipeline["name"])
		source.form_questions_mapping = {"full_name": "first_name", "email": "email"}
		lead = source.sync_single_lead(
			{
				"id": "fb-lead-intake-1",
				"field_data": [
					{"name": "full_name", "values": ["Carla"]},
					{"name": "email", "values": ["carla@example.com"]},
				],
			},
			raise_exception=True,
		)
		self.assertEqual(self.card_of(lead.name).pipeline, self.pipeline["name"])

	def test_lead_sync_source_needs_pipeline_when_enabled(self):
		doc = frappe.get_doc(
			{
				"doctype": "Lead Sync Source",
				"type": "Facebook",
				"access_token": "x",
				"enabled": 1,
				"background_sync_frequency": "Hourly",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_call_creates_card_in_pipeline(self):
		call = create_test_call_log(from_number="+5511999990000")
		card = create_lead_from_call_log(
			{"name": call.name}, {"first_name": "Dani"}, pipeline=self.pipeline["name"]
		)
		self.assertEqual(frappe.db.get_value("CRM Deal", card, "pipeline"), self.pipeline["name"])
		call.reload()
		self.assertTrue(call.has_link("CRM Deal", card))

	def test_call_needs_membership_of_pipeline(self):
		call = create_test_call_log(from_number="+5511999990001")
		frappe.set_user(OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			create_lead_from_call_log(
				{"name": call.name}, {"first_name": "Eva"}, pipeline=self.pipeline["name"]
			)

	def test_web_forms_seed_hidden_pipeline(self):
		for document_type in ("CRM Lead", "CRM Deal"):
			hidden = {f["fieldname"]: f for f in _seed_hidden_fields(document_type)}
			self.assertEqual(hidden["pipeline"]["default"], get_default_pipeline())
		self.assertNotIn("status", {f["fieldname"] for f in _seed_hidden_fields("CRM Deal")})

	def test_assignees_outside_pipeline_are_not_carried_over(self):
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Fabi"}).insert(ignore_permissions=True)
		assign_add({"assign_to": [OUTSIDER], "doctype": "CRM Lead", "name": lead.name})
		lead.reload()
		lead.pipeline = self.pipeline["name"]
		card = lead.convert_into_pipeline()
		assignees = frappe.get_all(
			"ToDo",
			{"reference_type": "CRM Deal", "reference_name": card, "status": "Open"},
			pluck="allocated_to",
		)
		self.assertNotIn(OUTSIDER, assignees)
