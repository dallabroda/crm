# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.api.forms import create_field, get_fields, get_form_schema, save_form_config
from crm.api.pipeline import get_field_catalog
from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.fcrm.doctype.crm_pipeline.form_schema import form_catalog
from crm.patches.credhub.move_company_fields_to_organization import copy_to_organizations
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"
ORG = "CRM Organization"


class TestGlobalForms(FrappeTestCase):
	"""Dynamic forms, phase 3 (credtech#181): organizations and contacts have their own catalog and one form
	each, with required fields; card fields that repeat the organization moved to it (decision 7)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# custom fields change the table (implicit commit): created once and removed at the end
		cls.created = create_field("Origem do contato teste", "Data", doctype="Contact")["fieldname"]
		frappe.db.commit()  # nosemgrep: custom fields are DDL and must persist for the class

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		name = frappe.db.get_value("Custom Field", {"dt": "Contact", "fieldname": cls.created})
		if name:
			frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
		frappe.db.delete("CRM Form Config", {"name": ("in", ("Contact", ORG))})
		frappe.db.commit()  # nosemgrep: persist cleanup of committed custom fields
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.local.form_dict.pop("cmd", None)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.form_dict.pop("cmd", None)
		frappe.db.rollback()

	def _schema(self, doctype):
		return {f["fieldname"]: f for f in get_form_schema(doctype)["fields"]}

	def test_organization_catalog_has_its_own_native_fields(self):
		names = {f["fieldname"]: f for f in form_catalog(ORG)}
		self.assertIn("website", names)
		self.assertIn("industry", names)
		self.assertNotIn("currency", names)
		self.assertEqual(names["organization_name"]["locked"], 1)
		if frappe.get_meta(ORG).has_field("cnpj"):
			# Receita Federal data (filled by the CNPJ lookup) are normal fields of the form
			self.assertEqual(names["cnpj"]["is_standard"], 1)
			self.assertNotIn("cnpj_checked_on", names)

	def test_before_saving_the_form_follows_the_side_panel(self):
		schema = get_form_schema("Contact")["fields"]
		self.assertEqual(schema[0]["fieldname"], "first_name")
		created = next(f for f in schema if f["fieldname"] == self.created)
		self.assertEqual((created["visible"], created["required"]), (1, 0))

	def test_saved_form_order_visible_and_required(self):
		save_form_config(
			"Contact",
			[
				{"fieldname": "mobile_no", "visible": 1, "required": 0},
				{"fieldname": self.created, "visible": 0},
				{"fieldname": "designation", "required": 1},
			],
		)
		schema = get_form_schema("Contact")["fields"]
		names = [f["fieldname"] for f in schema]
		self.assertEqual(names[:4], ["first_name", "mobile_no", self.created, "designation"])
		by_name = {f["fieldname"]: f for f in schema}
		self.assertEqual(by_name[self.created]["visible"], 0)
		# required implies visible
		self.assertEqual((by_name["designation"]["visible"], by_name["designation"]["required"]), (1, 1))

	def test_system_filled_fields_cannot_be_required(self):
		read_only = next((f for f in form_catalog(ORG) if not f["can_require"]), None)
		if not read_only:
			self.skipTest("no read-only field in the organization form")
		with self.assertRaises(frappe.ValidationError):
			save_form_config(ORG, [{"fieldname": read_only["fieldname"], "required": 1}])

	def test_only_admins_change_the_form(self):
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			save_form_config(ORG, [{"fieldname": "website"}])

	def test_required_when_created_directly_not_as_a_side_effect(self):
		save_form_config(ORG, [{"fieldname": "website", "required": 1}])
		# created as part of another flow (lead conversion, card with a new company): not blocked
		side = frappe.get_doc({"doctype": ORG, "organization_name": "Side Effect Test Org"}).insert()
		# created from its own form or the REST API: the required field is asked
		frappe.local.form_dict.cmd = "frappe.client.insert"
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": ORG, "organization_name": "Direct Test Org"}).insert()
		frappe.get_doc(
			{"doctype": ORG, "organization_name": "Direct Ok Test Org", "website": "https://ok.example.test"}
		).insert()
		# automatic entries are never blocked
		frappe.flags.crm_automatic_entry = True
		try:
			frappe.get_doc({"doctype": ORG, "organization_name": "Automatic Test Org"}).insert()
		finally:
			frappe.flags.crm_automatic_entry = False
		frappe.local.form_dict.pop("cmd", None)
		# a record saved before the rule is not blocked on other edits
		side.industry = None
		side.save()

	def test_a_filled_required_field_cannot_be_emptied(self):
		org = frappe.get_doc(
			{"doctype": ORG, "organization_name": "Emptied Test Org", "website": "https://x.example.test"}
		).insert()
		save_form_config(ORG, [{"fieldname": "website", "required": 1}])
		org.website = ""
		with self.assertRaises(frappe.ValidationError):
			org.save()

	def test_card_fields_that_repeat_the_organization_left_the_card(self):
		catalog = {f["fieldname"] for f in get_field_catalog()["fields"]}
		moved = {f["fieldname"] for f in get_field_catalog()["moved"]}
		for field in field_catalog.MOVED_TO_ORGANIZATION:
			self.assertNotIn(field, catalog)
			self.assertIn(field, moved)
		self.assertNotIn("website", field_catalog.default_pipeline_fields())

	def test_card_values_go_to_the_organization_without_replacing(self):
		filled = frappe.get_doc(
			{
				"doctype": ORG,
				"organization_name": "Filled Copy Test Org",
				"website": "https://keep.example.test",
			}
		).insert()
		empty = frappe.get_doc({"doctype": ORG, "organization_name": "Empty Copy Test Org"}).insert()
		for org, website, modified in (
			(empty.name, "https://old.example.test", "2026-01-01 10:00:00"),
			(empty.name, "https://new.example.test", "2026-06-01 10:00:00"),
			(filled.name, "https://other.example.test", "2026-06-01 10:00:00"),
		):
			card = frappe.get_doc(
				{"doctype": "CRM Deal", "organization": org, "website": website, "status": "Qualification"}
			)
			card.flags.ignore_mandatory = True
			card.insert(ignore_permissions=True)
			frappe.db.set_value("CRM Deal", card.name, "modified", modified, update_modified=False)
		copy_to_organizations()
		# the most recently changed card wins; a filled organization field is never replaced
		self.assertEqual(frappe.db.get_value(ORG, empty.name, "website"), "https://new.example.test")
		self.assertEqual(frappe.db.get_value(ORG, filled.name, "website"), "https://keep.example.test")

	def test_fields_of_each_form_for_the_screen(self):
		contact = get_fields("Contact")
		self.assertEqual(contact["limit"], field_catalog.CREATED_FIELD_LIMIT)
		self.assertIn(self.created, {f["fieldname"] for f in contact["fields"]})

	def test_contact_email_and_phone_can_be_required(self):
		# read-only in the doctype, but filled from the contact's e-mails and phones
		save_form_config("Contact", [{"fieldname": "email_id", "required": 1}])
		self.assertTrue(get_form_schema("Contact")["configured"])
		frappe.local.form_dict.cmd = "frappe.client.insert"
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc({"doctype": "Contact", "first_name": "Sem Email Teste"}).insert()
		frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Com Email Teste",
				"email_ids": [{"email_id": "com.email@example.test", "is_primary": 1}],
			}
		).insert()
