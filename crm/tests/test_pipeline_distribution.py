# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.api.pipeline import get_pipeline_config, save_pipeline
from crm.fcrm.doctype.crm_pipeline.distribution import pick_salesperson
from crm.tests import CRMTestCase as FrappeTestCase

SELLERS = ["crm.user1@example.com", "crm.user2@example.com", "crm.user3@example.com"]
OWNER = "crm.manager@example.com"


class TestPipelineDistribution(FrappeTestCase):
	"""Cards that arrive on their own go to a salesperson by the pipeline's rule (credtech#51)."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Distribution",
				"stages": [{"deal_status": "New"}, {"deal_status": "Won", "type": "Won"}],
				"members": [{"user": OWNER, "role": "Owner"}]
				+ [{"user": u, "role": "Member"} for u in SELLERS],
			}
		)["name"]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for name in frappe.get_all("CRM Pipeline", {"pipeline_name": "Distribution"}, pluck="name"):
			for card in frappe.get_all("CRM Deal", {"pipeline": name}, pluck="name"):
				frappe.db.delete("ToDo", {"reference_type": "CRM Deal", "reference_name": card})
				frappe.delete_doc("CRM Deal", card, force=True, ignore_permissions=True)
			frappe.delete_doc("CRM Pipeline", name, force=True, ignore_permissions=True)
		frappe.db.commit()  # nosemgrep: card inserts commit, so clean up explicitly

	def configure(self, distribution):
		save_pipeline({"name": self.pipeline, "distribution": distribution})

	def test_round_robin_between_sellers_by_default(self):
		picks = [pick_salesperson(self.pipeline, {}) for _ in range(4)]
		self.assertEqual(picks, SELLERS + SELLERS[:1])

	def test_round_robin_subset(self):
		self.configure({"mode": "round_robin", "round_robin_users": SELLERS[1:]})
		self.assertEqual(
			[pick_salesperson(self.pipeline, {}) for _ in range(3)], [SELLERS[1], SELLERS[2], SELLERS[1]]
		)

	def test_rules_first_match_ignores_case_and_spaces(self):
		self.configure(
			{
				"mode": "rules",
				"rules": [
					{"field": "territory", "value": "SP", "user": SELLERS[2]},
					{"field": "source", "value": "Facebook", "user": SELLERS[1]},
				],
				"fallback": "owner",
			}
		)
		self.assertEqual(
			pick_salesperson(self.pipeline, {"territory": " sp ", "source": "Facebook"}), SELLERS[2]
		)
		self.assertEqual(pick_salesperson(self.pipeline, {"source": "facebook"}), SELLERS[1])
		self.assertEqual(pick_salesperson(self.pipeline, {"source": "Google"}), OWNER)  # fallback dono

	def test_user_who_left_is_skipped(self):
		self.configure(
			{"mode": "rules", "rules": [{"field": "source", "value": "x", "user": "fora@example.com"}]}
		)
		self.assertIn(pick_salesperson(self.pipeline, {"source": "x"}), SELLERS)

	def test_no_seller_goes_to_owner(self):
		save_pipeline({"name": self.pipeline, "members": [{"user": OWNER, "role": "Owner"}]})
		self.assertEqual(pick_salesperson(self.pipeline, {}), OWNER)

	def test_config_round_trip_drops_incomplete_rules(self):
		self.configure(
			{"mode": "rules", "rules": [{"field": "source", "value": "", "user": SELLERS[0]}], "bad": 1}
		)
		self.assertEqual(
			get_pipeline_config(self.pipeline)["distribution"],
			{"mode": "rules", "round_robin_users": [], "rules": [], "fallback": "round_robin"},
		)

	def test_automatic_entry_is_assigned(self):
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Bia", "pipeline": self.pipeline, "source": "Facebook"}
		).insert(ignore_permissions=True)
		card = frappe.get_doc("CRM Deal", {"lead": lead.name})
		self.assertIn(card.deal_owner, SELLERS)

	def test_same_person_with_open_card_gets_no_new_card(self):
		first = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Bia",
				"pipeline": self.pipeline,
				"email": "bia@example.com",
			}
		).insert(ignore_permissions=True)
		card = frappe.db.get_value("CRM Deal", {"lead": first.name})
		again = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Bia",
				"pipeline": self.pipeline,
				"email": "BIA@example.com",
				"source": "Facebook",
			}
		).insert(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("CRM Deal", {"lead": again.name}))
		self.assertEqual(again.flags.duplicate_of, card)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{"reference_doctype": "CRM Deal", "reference_name": card, "comment_type": "Comment"},
			)
		)
		owner = frappe.db.get_value("CRM Deal", card, "deal_owner")
		self.assertTrue(frappe.db.exists("CRM Notification", {"to_user": owner, "reference_name": card}))

	def test_graph_list_follows_every_page(self):
		from unittest.mock import patch

		from crm.lead_syncing.doctype.lead_sync_source import facebook

		pages = [
			{"data": [{"id": 1}, {"id": 2}], "paging": {"next": "https://graph.test/next"}},
			{"data": [{"id": 3}]},
		]
		with patch.object(facebook, "make_get_request", side_effect=pages):
			self.assertEqual([i["id"] for i in facebook.get_all_pages("https://graph.test", {})], [1, 2, 3])

	def test_repeat_does_not_use_a_round_robin_turn(self):
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Bia",
				"pipeline": self.pipeline,
				"email": "bia@example.com",
			}
		).insert(ignore_permissions=True)  # 1º vendedor
		frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Bia",
				"pipeline": self.pipeline,
				"email": "bia@example.com",
			}
		).insert(ignore_permissions=True)  # repetido: não gasta a vez
		self.assertEqual(pick_salesperson(self.pipeline, {}), SELLERS[1])

	def test_same_digits_other_area_code_is_another_person(self):
		def lead(mobile):
			return frappe.get_doc(
				{"doctype": "CRM Lead", "first_name": "Cia", "pipeline": self.pipeline, "mobile_no": mobile}
			).insert(ignore_permissions=True)

		first = lead("+55 (48) 99999-0000")
		other_area = lead("(38) 99999-0000")
		same = lead("48999990000")
		self.assertTrue(frappe.db.exists("CRM Deal", {"lead": other_area.name}))
		self.assertEqual(same.flags.duplicate_of, frappe.db.get_value("CRM Deal", {"lead": first.name}))
