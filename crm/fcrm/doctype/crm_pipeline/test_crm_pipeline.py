# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.api.dashboard import label_stages
from crm.api.pipeline import change_pipeline, get_pipeline_config, get_pipelines, move_card, save_pipeline
from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline, get_first_stage
from crm.tests import CRMTestCase as FrappeTestCase

SALES_USER = "crm.user1@example.com"


def make_pipeline(name="Credit", stages=("Lead", "Analysis", "Won", "Lost"), members=None):
	types = {"Won": "Won", "Lost": "Lost"}
	return save_pipeline(
		{
			"pipeline_name": name,
			"stages": [{"deal_status": s, "type": types.get(s, "Open")} for s in stages],
			"members": members or [],
		}
	)


def make_card(**kwargs):
	return frappe.get_doc({"doctype": "CRM Deal", "deal_owner": "Administrator", **kwargs}).insert()


class TestCRMPipeline(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_default_pipeline_holds_default_stages(self):
		default = get_default_pipeline()
		self.assertTrue(default)
		self.assertEqual(frappe.db.get_value("CRM Deal Status", "Qualification", "pipeline"), default)

	def test_card_without_pipeline_is_refused(self):
		# Pipeline is mandatory and never guessed (owner decision)
		with self.assertRaises(frappe.MandatoryError):
			frappe.get_doc({"doctype": "CRM Deal", "deal_owner": "Administrator"}).insert()

	def test_card_takes_first_stage_of_its_pipeline(self):
		card = make_card(pipeline=get_default_pipeline())
		self.assertEqual(card.status, get_first_stage(card.pipeline))

	def test_card_gets_pipeline_from_stage(self):
		credit = make_pipeline()
		analysis = credit["stages"][1]["name"]
		card = make_card(status=analysis)
		self.assertEqual(card.pipeline, credit["name"])

	def test_same_stage_name_in_two_pipelines(self):
		a = make_pipeline("A", stages=("Qualification", "Won"))
		b = make_pipeline("B", stages=("Qualification", "Won"))
		self.assertNotEqual(a["stages"][0]["name"], b["stages"][0]["name"])

	def test_duplicate_stage_name_in_pipeline_is_rejected(self):
		with self.assertRaises(frappe.DuplicateEntryError):
			make_pipeline(stages=("Lead", "Lead"))

	def test_stage_from_other_pipeline_is_rejected(self):
		credit = make_pipeline()
		with self.assertRaises(frappe.ValidationError):
			make_card(pipeline=get_default_pipeline(), status=credit["stages"][0]["name"])

	def test_inactive_pipeline_rejects_new_cards(self):
		credit = make_pipeline()
		frappe.db.set_value("CRM Pipeline", credit["name"], "is_active", 0)
		with self.assertRaises(frappe.ValidationError):
			make_card(pipeline=credit["name"])

	def test_stages_follow_payload_order(self):
		credit = make_pipeline(stages=("One", "Two", "Three"))
		stages = credit["stages"]
		reordered = save_pipeline({"name": credit["name"], "stages": [stages[2], stages[0], stages[1]]})
		self.assertEqual([s["deal_status"] for s in reordered["stages"]], ["Three", "One", "Two"])
		self.assertEqual([s["position"] for s in reordered["stages"]], [1, 2, 3])

	def test_change_pipeline_keeps_values_and_logs_pipeline(self):
		credit = make_pipeline()
		card = make_card(pipeline=get_default_pipeline(), next_step="Call back")
		change_pipeline(card.name, credit["name"])
		card.reload()
		self.assertEqual(card.pipeline, credit["name"])
		self.assertEqual(card.status, credit["stages"][0]["name"])
		self.assertEqual(card.next_step, "Call back")
		self.assertEqual(card.status_change_log[-1].pipeline, credit["name"])
		self.assertEqual(card.status_change_log[-2].pipeline, get_default_pipeline())

	def test_move_card_sets_stage_and_values(self):
		credit = make_pipeline()
		card = make_card(pipeline=credit["name"])
		move_card(card.name, credit["stages"][1]["name"], {"next_step": "Send documents"})
		card.reload()
		self.assertEqual(card.status, credit["stages"][1]["name"])
		self.assertEqual(card.next_step, "Send documents")

	def test_move_card_rejects_protected_fields(self):
		credit = make_pipeline()
		card = make_card(pipeline=credit["name"])
		with self.assertRaises(frappe.ValidationError):
			move_card(card.name, credit["stages"][1]["name"], {"pipeline": get_default_pipeline()})

	def test_move_card_rejects_read_only_fields(self):
		credit = make_pipeline()
		card = make_card(pipeline=credit["name"])
		with self.assertRaises(frappe.ValidationError):
			move_card(card.name, credit["stages"][1]["name"], {"sla_status": "Fulfilled"})

	def test_swapping_stage_names(self):
		credit = make_pipeline(stages=("One", "Two"))
		one, two = credit["stages"]
		saved = save_pipeline(
			{"name": credit["name"], "stages": [{**one, "deal_status": "Two"}, {**two, "deal_status": "One"}]}
		)
		self.assertEqual([s["deal_status"] for s in saved["stages"]], ["Two", "One"])
		self.assertEqual([s["name"] for s in saved["stages"]], [one["name"], two["name"]])

	def test_stage_with_cards_cannot_be_removed(self):
		credit = make_pipeline()
		make_card(pipeline=credit["name"])
		with self.assertRaises(frappe.ValidationError):
			save_pipeline({"name": credit["name"], "stages": credit["stages"][1:]})

	def test_empty_stage_is_removed(self):
		credit = make_pipeline()
		removed = credit["stages"][0]["name"]
		save_pipeline({"name": credit["name"], "stages": credit["stages"][1:]})
		self.assertFalse(frappe.db.exists("CRM Deal Status", removed))

	def test_pipeline_with_cards_cannot_be_deleted(self):
		credit = make_pipeline()
		make_card(pipeline=credit["name"])
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("CRM Pipeline", credit["name"])

	def test_deleting_empty_pipeline_removes_its_stages(self):
		credit = make_pipeline()
		frappe.delete_doc("CRM Pipeline", credit["name"])
		self.assertFalse(frappe.db.exists("CRM Deal Status", {"pipeline": credit["name"]}))

	def test_sales_user_only_sees_pipelines_they_belong_to(self):
		member_of = make_pipeline("Mine", members=[{"user": SALES_USER, "role": "Member"}])
		other = make_pipeline("Other")
		frappe.set_user(SALES_USER)
		visible = {p["name"]: p["my_role"] for p in get_pipelines()}
		self.assertEqual(visible.get(member_of["name"]), "Member")
		self.assertNotIn(other["name"], visible)
		with self.assertRaises(frappe.PermissionError):
			get_pipeline_config(other["name"])

	def test_member_cannot_change_pipeline(self):
		credit = make_pipeline(members=[{"user": SALES_USER, "role": "Member"}])
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			save_pipeline({"name": credit["name"], "pipeline_name": "Renamed"})

	def test_duplicate_member_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			make_pipeline(members=[{"user": SALES_USER}, {"user": SALES_USER}])

	def test_dashboard_labels_stages_with_pipeline_when_many(self):
		credit = make_pipeline()
		rows = label_stages([{"stage": credit["stages"][0]["name"], "count": 1}])
		self.assertEqual(rows[0]["stage"], "Credit · Lead")
