# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

from unittest.mock import patch

import frappe

from crm.api.pipeline import (
	create_field,
	disable_field,
	get_field_catalog,
	get_missing_fields,
	get_stage_rules,
	move_card,
	save_pipeline,
	update_field,
)
from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.fcrm.doctype.crm_pipeline.fields import MissingRequiredFieldsError
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"


class TestPipelineFields(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Custom fields change the table (implicit commit), so they are created once and removed at the end
		cls.cpf = create_field("CPF test", "Data")["fieldname"]
		cls.kind = create_field("Kind test", "Select", "Person\nCompany")["fieldname"]
		frappe.db.commit()  # nosemgrep: custom fields are DDL and must persist for the class

	@classmethod
	def tearDownClass(cls):
		for fieldname in (cls.cpf, cls.kind):
			name = frappe.db.get_value("Custom Field", {"dt": "CRM Deal", "fieldname": fieldname})
			if name:
				frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
		frappe.db.commit()  # nosemgrep: persist cleanup of committed custom fields
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Credit fields",
				"stages": [
					{"deal_status": "Lead"},
					{"deal_status": "Documents"},
					{"deal_status": "Won", "type": "Won"},
				],
				"fields": [self.cpf, self.kind, "next_step"],
			}
		)
		self.lead, self.documents, self.won = (s["name"] for s in self.pipeline["stages"])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		# Card inserts commit, so remove what the test left behind
		for pipeline in frappe.get_all(
			"CRM Pipeline", {"pipeline_name": ("in", ("Credit fields", "Defaults"))}, pluck="name"
		):
			for card in frappe.get_all("CRM Deal", {"pipeline": pipeline}, pluck="name"):
				frappe.db.delete("ToDo", {"reference_type": "CRM Deal", "reference_name": card})
				frappe.delete_doc("CRM Deal", card, force=True, ignore_permissions=True)
			frappe.delete_doc("CRM Pipeline", pipeline, force=True, ignore_permissions=True)
		frappe.db.commit()  # nosemgrep: persist per-test cleanup of committed fixtures

	def make_card(self, **kwargs):
		return frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"pipeline": self.pipeline["name"],
				"deal_owner": "Administrator",
				**kwargs,
			}
		).insert()

	def set_rule(self, stage, fieldname, **rule):
		save_pipeline(
			{"name": self.pipeline["name"], "field_rules": [{"stage": stage, "fieldname": fieldname, **rule}]}
		)

	# Catalog ----------------------------------------------------------------

	def test_catalog_lists_locked_standard_and_created_fields(self):
		catalog = {f["fieldname"]: f for f in get_field_catalog()["fields"]}
		self.assertEqual(catalog["pipeline"]["locked"], 1)
		self.assertEqual(catalog["organization"]["is_standard"], 1)
		self.assertEqual(catalog[self.cpf]["is_standard"], 0)
		self.assertTrue(self.cpf.startswith(field_catalog.CREATED_PREFIX))
		self.assertEqual(catalog[self.kind]["options"], "Person\nCompany")

	def test_catalog_limit(self):
		with patch.object(field_catalog, "CREATED_FIELD_LIMIT", field_catalog.created_field_count()):
			with self.assertRaises(frappe.ValidationError):
				create_field("One too many", "Data")

	def test_field_type_validation(self):
		for args in (("Bad type", "Table"), ("No options", "Select", ""), ("Bad link", "Link", "User")):
			with self.assertRaises(frappe.ValidationError):
				create_field(*args)

	def test_only_admins_change_the_catalog(self):
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			create_field("Nope", "Data")
		with self.assertRaises(frappe.PermissionError):
			update_field(self.cpf, label="Renamed")

	def test_deleted_field_is_dropped_from_pipelines(self):
		gone = create_field("Gone test", "Data")["fieldname"]
		save_pipeline({"name": self.pipeline["name"], "fields": [self.cpf, gone]})
		name = frappe.db.get_value("Custom Field", {"dt": "CRM Deal", "fieldname": gone})
		frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
		frappe.clear_cache(doctype="CRM Deal")
		config = save_pipeline({"name": self.pipeline["name"], "pipeline_name": "Credit fields"})
		self.assertEqual([f["fieldname"] for f in config["fields"]], [self.cpf])
		self.assertNotIn(gone, {r["fieldname"] for r in config["field_rules"]})

	def test_disabled_field_stays_in_pipelines_that_use_it(self):
		disable_field(self.kind)
		try:
			config = save_pipeline({"name": self.pipeline["name"], "pipeline_name": "Credit fields"})
			self.assertIn(self.kind, [f["fieldname"] for f in config["fields"]])
		finally:
			enable_field(self.kind)

	def test_update_and_disable_field(self):
		self.assertEqual(update_field(self.kind, label="Kind renamed")["label"], "Kind renamed")
		self.assertEqual(update_field(self.kind, options="A\nB")["options"], "A\nB")
		update_field(self.kind, label="Kind test", options="Person\nCompany")
		self.assertTrue(disable_field(self.kind)["disabled"])
		self.assertNotIn(self.kind, field_catalog.catalog_fieldnames())
		with self.assertRaises(frappe.ValidationError):
			save_pipeline(
				{"pipeline_name": "Uses disabled", "fields": [self.kind], "stages": [{"deal_status": "A"}]}
			)
		enable_field(self.kind)

	def test_standard_fields_cannot_be_changed(self):
		with self.assertRaises(frappe.ValidationError):
			update_field("organization", label="Company")

	# Pipeline fields and rules -----------------------------------------------

	def test_new_pipeline_starts_with_standard_fields_and_full_matrix(self):
		created = save_pipeline(
			{"pipeline_name": "Defaults", "stages": [{"deal_status": "A"}, {"deal_status": "B"}]}
		)
		fieldnames = [f["fieldname"] for f in created["fields"]]
		self.assertEqual(fieldnames, field_catalog.default_pipeline_fields())
		self.assertEqual(len(created["field_rules"]), len(fieldnames) * 2)
		self.assertTrue(
			all(r["visible"] and not r["required"] and not r["read_only"] for r in created["field_rules"])
		)

	def test_rules_follow_fields_and_stages(self):
		config = save_pipeline(
			{
				"name": self.pipeline["name"],
				"fields": [self.cpf],
				"stages": [*self.pipeline["stages"][:2], {"deal_status": "Signed"}],
			}
		)
		pairs = {(r["stage"], r["fieldname"]) for r in config["field_rules"]}
		self.assertEqual(len(pairs), 3)
		self.assertTrue(all(fieldname == self.cpf for _, fieldname in pairs))
		self.assertNotIn(self.won, {stage for stage, _ in pairs})

	def test_locked_and_unknown_fields_are_rejected(self):
		for fieldname in ("status", "not_a_field"):
			with self.assertRaises(frappe.ValidationError):
				save_pipeline({"name": self.pipeline["name"], "fields": [fieldname]})

	def test_required_field_must_be_visible(self):
		with self.assertRaises(frappe.ValidationError):
			self.set_rule(self.documents, self.cpf, visible=0, required=1)

	def test_stage_rules_api(self):
		self.set_rule(self.documents, self.cpf, required=1)
		rules = get_stage_rules(self.pipeline["name"], self.documents)
		self.assertEqual(rules[self.cpf], {"visible": 1, "required": 1, "read_only": 0})
		self.assertEqual(rules["next_step"]["required"], 0)

	# Card validation ----------------------------------------------------------

	def test_entering_stage_needs_its_required_fields(self):
		self.set_rule(self.documents, self.cpf, required=1)
		card = self.make_card()
		self.assertEqual([m["fieldname"] for m in get_missing_fields(card.name, self.documents)], [self.cpf])
		with self.assertRaises(MissingRequiredFieldsError):
			move_card(card.name, self.documents)
		self.assertEqual(frappe.local.response["missing_fields"][0]["fieldname"], self.cpf)
		move_card(card.name, self.documents, {self.cpf: "123.456.789-00"})
		self.assertEqual(frappe.db.get_value("CRM Deal", card.name, "status"), self.documents)

	def test_new_card_needs_required_fields_of_its_stage(self):
		self.set_rule(self.lead, self.cpf, required=1)
		with self.assertRaises(MissingRequiredFieldsError):
			self.make_card()
		self.assertTrue(self.make_card(**{self.cpf: "1"}).name)

	def test_read_only_field_cannot_change_in_that_stage(self):
		self.set_rule(self.documents, self.cpf, read_only=1)
		card = self.make_card(**{self.cpf: "1"})
		card.next_step = "Call"
		card.save()  # other fields are fine
		move_card(card.name, self.documents)
		card.reload()
		card.set(self.cpf, "2")
		with self.assertRaises(frappe.ValidationError):
			card.save()
		card.reload()
		with self.assertRaises(frappe.ValidationError):
			move_card(card.name, self.won, {self.cpf: "3"})  # still in the read-only stage while saving
		move_card(card.name, self.won)
		card.reload()
		card.set(self.cpf, "3")
		card.save()  # editable again in the next stage

	def test_read_only_ignores_same_value_in_another_format(self):
		date_field = create_field("Date test", "Date")["fieldname"]
		try:
			save_pipeline({"name": self.pipeline["name"], "fields": [self.cpf, date_field]})
			self.set_rule(self.lead, date_field, read_only=1)
			card = self.make_card(**{date_field: "2026-10-24"})
			card.reload()
			card.set(date_field, "2026-10-24")
			card.save()
		finally:
			frappe.db.rollback()
			name = frappe.db.get_value("Custom Field", {"dt": "CRM Deal", "fieldname": date_field})
			frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
			frappe.db.commit()  # nosemgrep: persist cleanup of committed custom field


def enable_field(fieldname):
	# Saving a Custom Field may commit (schema sync), so undo a disable explicitly and persist it
	cf = frappe.get_doc("Custom Field", {"dt": "CRM Deal", "fieldname": fieldname})
	cf.hidden = 0
	cf.save(ignore_permissions=True)
	frappe.clear_cache(doctype="CRM Deal")
	frappe.db.commit()  # nosemgrep: custom field state must survive the test rollback
