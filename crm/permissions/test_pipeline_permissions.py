# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe
from frappe.desk.form.assign_to import add as assign_add

from crm.api.dashboard import get_chart
from crm.api.pipeline import get_pipeline_users, save_pipeline, set_pipeline_owner_role
from crm.patches.credhub.add_pipeline_permissions import execute as add_pipeline_permissions
from crm.permissions.pipeline import has_deal_permission, is_admin
from crm.tests import CRMTestCase as FrappeTestCase

ADMIN = "admin@pipe.test"
OWNER = "owner@pipe.test"
REP1 = "rep1@pipe.test"
REP2 = "rep2@pipe.test"
OUTSIDER = "outsider@pipe.test"
TEST_USERS = (ADMIN, OWNER, REP1, REP2, OUTSIDER)


class TestPipelinePermissions(FrappeTestCase):
	"""
	Pipeline "Credit": OWNER (Owner), REP1 and REP2 (Member). OUTSIDER is in no pipeline.
	ADMIN is a Sales Manager outside the sales hierarchy.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user(ADMIN, ["Sales Manager", "Sales User"])
		make_user(OWNER, ["Sales User", "Pipeline Owner"])
		for user in (REP1, REP2, OUTSIDER):
			make_user(user, ["Sales User"])
		frappe.db.commit()  # nosemgrep: fixtures must persist across the committing after_insert hooks

	@classmethod
	def tearDownClass(cls):
		for email in TEST_USERS:
			frappe.db.delete("CRM Pipeline Member", {"user": email})
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()  # nosemgrep: persist teardown cleanup of committed fixtures
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Credit",
				"stages": [{"deal_status": "Lead"}, {"deal_status": "Analysis"}],
				"members": [
					{"user": OWNER, "role": "Owner"},
					{"user": REP1, "role": "Member"},
					{"user": REP2, "role": "Member"},
				],
			}
		)["name"]
		self.card_rep1 = make_card(self.pipeline, REP1)
		self.card_rep2 = make_card(self.pipeline, REP2)

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in frappe.get_all("CRM Deal", {"pipeline": self.pipeline}, pluck="name"):
			frappe.db.delete("ToDo", {"reference_type": "CRM Deal", "reference_name": name})
			frappe.db.delete("DocShare", {"share_doctype": "CRM Deal", "share_name": name})
			frappe.delete_doc("CRM Deal", name, force=True, ignore_permissions=True)
		frappe.delete_doc("CRM Pipeline", self.pipeline, force=True, ignore_permissions=True)
		frappe.db.commit()  # nosemgrep: persist per-test cleanup of committed fixtures

	def visible_cards(self, user):
		frappe.set_user(user)
		cards = set(frappe.get_list("CRM Deal", {"pipeline": self.pipeline}, pluck="name"))
		frappe.set_user("Administrator")
		return cards

	# Cards ------------------------------------------------------------------

	def test_member_sees_only_own_cards(self):
		self.assertEqual(self.visible_cards(REP1), {self.card_rep1})
		self.assertTrue(has_deal_permission(frappe.get_doc("CRM Deal", self.card_rep1), "read", REP1))
		self.assertFalse(has_deal_permission(frappe.get_doc("CRM Deal", self.card_rep2), "read", REP1))

	def test_owner_sees_every_card_of_the_pipeline(self):
		self.assertEqual(self.visible_cards(OWNER), {self.card_rep1, self.card_rep2})

	def test_admin_sees_everything(self):
		self.assertTrue(is_admin(ADMIN))
		self.assertEqual(self.visible_cards(ADMIN), {self.card_rep1, self.card_rep2})

	def test_outsider_sees_nothing(self):
		self.assertEqual(self.visible_cards(OUTSIDER), set())
		self.assertFalse(has_deal_permission(frappe.get_doc("CRM Deal", self.card_rep1), "read", OUTSIDER))

	def test_member_sees_card_assigned_to_them(self):
		assign_add({"assign_to": [REP1], "doctype": "CRM Deal", "name": self.card_rep2})
		self.assertEqual(self.visible_cards(REP1), {self.card_rep1, self.card_rep2})

	def test_card_cannot_be_assigned_outside_the_pipeline(self):
		with self.assertRaises(frappe.ValidationError):
			assign_add({"assign_to": [OUTSIDER], "doctype": "CRM Deal", "name": self.card_rep1})

	def test_responsible_must_be_a_member(self):
		with self.assertRaises(frappe.ValidationError):
			make_card(self.pipeline, OUTSIDER)

	def test_non_member_cannot_create_card_in_pipeline(self):
		frappe.set_user(OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({"doctype": "CRM Deal", "pipeline": self.pipeline, "deal_owner": REP1}).insert()

	def test_member_can_create_card_in_pipeline(self):
		frappe.set_user(REP1)
		card = frappe.get_doc({"doctype": "CRM Deal", "pipeline": self.pipeline, "deal_owner": REP1}).insert()
		self.assertEqual(card.pipeline, self.pipeline)

	def test_api_list_respects_pipeline_rules(self):
		frappe.set_user(REP2)
		cards = {d.name for d in frappe.client.get_list("CRM Deal", filters={"pipeline": self.pipeline})}
		self.assertEqual(cards, {self.card_rep2})

	# Pipelines and stages ---------------------------------------------------

	def test_members_only_see_their_pipelines_and_stages(self):
		frappe.set_user(OUTSIDER)
		self.assertNotIn(self.pipeline, frappe.get_list("CRM Pipeline", pluck="name"))
		self.assertFalse(frappe.get_list("CRM Deal Status", {"pipeline": self.pipeline}, pluck="name"))
		frappe.set_user(REP1)
		self.assertIn(self.pipeline, frappe.get_list("CRM Pipeline", pluck="name"))
		self.assertTrue(frappe.get_list("CRM Deal Status", {"pipeline": self.pipeline}, pluck="name"))

	def test_only_owners_change_pipeline_and_stages(self):
		pipeline = frappe.get_doc("CRM Pipeline", self.pipeline)
		stage = frappe.get_doc("CRM Deal Status", {"pipeline": self.pipeline})
		self.assertFalse(frappe.has_permission("CRM Pipeline", "write", pipeline, user=REP1))
		self.assertFalse(frappe.has_permission("CRM Deal Status", "write", stage, user=REP1))
		self.assertTrue(frappe.has_permission("CRM Pipeline", "write", pipeline, user=OWNER))
		self.assertTrue(frappe.has_permission("CRM Deal Status", "write", stage, user=OWNER))

	def test_pipeline_owner_role_creates_and_owns_pipeline(self):
		frappe.set_user(OWNER)
		created = save_pipeline({"pipeline_name": "Mine", "stages": [{"deal_status": "New"}]})
		frappe.set_user("Administrator")
		self.assertEqual(created["my_role"], "Owner")
		frappe.delete_doc("CRM Pipeline", created["name"], force=True, ignore_permissions=True)

	def test_sales_user_cannot_create_pipeline(self):
		frappe.set_user(REP1)
		with self.assertRaises(frappe.PermissionError):
			save_pipeline({"pipeline_name": "Nope", "stages": [{"deal_status": "New"}]})

	def test_owner_member_needs_pipeline_owner_role(self):
		with self.assertRaises(frappe.ValidationError):
			save_pipeline({"name": self.pipeline, "members": [{"user": REP1, "role": "Owner"}]})

	def test_pipeline_owner_role_is_managed_by_admins(self):
		frappe.set_user(OWNER)
		with self.assertRaises(frappe.PermissionError):
			set_pipeline_owner_role(REP1, True)
		frappe.set_user(ADMIN)
		self.assertTrue(set_pipeline_owner_role(REP1, True)["pipeline_owner"])
		self.assertFalse(set_pipeline_owner_role(REP1, False)["pipeline_owner"])
		with self.assertRaises(frappe.ValidationError):
			set_pipeline_owner_role(OWNER, False)  # still owns "Credit"

	def test_dashboard_gives_non_admins_only_their_numbers(self):
		def total(user, as_user):
			frappe.set_user(user)
			data = get_chart("deals_by_stage_donut", "donut", user=as_user)["data"]
			frappe.set_user("Administrator")
			return sum(row["count"] for row in data if row["stage"].startswith("Credit"))

		self.assertEqual(total(REP1, REP2), 1)  # asking for someone else's numbers returns their own
		self.assertEqual(total(ADMIN, None), 2)

	def test_pipeline_users_lists_who_can_own(self):
		frappe.set_user(ADMIN)
		data = get_pipeline_users()
		users = {u["name"]: u for u in data["users"]}
		self.assertTrue(data["can_create"])
		self.assertEqual(users[OWNER]["pipeline_owner"], 1)
		self.assertEqual(users[REP1]["pipeline_owner"], 0)
		self.assertEqual(users[ADMIN]["is_admin"], 1)
		frappe.set_user(REP1)
		self.assertFalse(get_pipeline_users()["can_create"])

	def test_patch_keeps_access_of_existing_users(self):
		save_pipeline({"name": self.pipeline, "members": []})
		add_pipeline_permissions()
		members = {m.user for m in frappe.get_doc("CRM Pipeline", self.pipeline).members}
		self.assertTrue({OWNER, REP1, REP2, OUTSIDER} <= members)


def make_user(email, roles):
	if frappe.db.exists("User", email):
		return
	user = frappe.get_doc(
		{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
	).insert(ignore_permissions=True)
	user.add_roles(*roles)


def make_card(pipeline, owner):
	return (
		frappe.get_doc({"doctype": "CRM Deal", "pipeline": pipeline, "deal_owner": owner})
		.insert(ignore_permissions=True)
		.name
	)
