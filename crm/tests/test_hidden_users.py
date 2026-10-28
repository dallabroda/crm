# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

from unittest.mock import patch

import frappe

from crm.api.pipeline import get_pipeline_config, get_pipeline_users, save_pipeline
from crm.api.session import get_users
from crm.fcrm.doctype.crm_pipeline.distribution import pick_salesperson
from crm.tests import CRMTestCase as FrappeTestCase
from crm.utils.hidden_users import hidden_users

SELLERS = ["crm.user1@example.com", "crm.user2@example.com"]
TECH = "api-hidden@example.com"


def _technical_users():
	return [TECH]


class TestHiddenUsers(FrappeTestCase):
	"""Users listed by the `crm_hidden_users` hook (API keys, credtech#175) stay out of the CRM lists,
	the pipeline members and the distribution, but keep their pipeline membership."""

	def setUp(self):
		frappe.set_user("Administrator")
		original = frappe.get_hooks

		def get_hooks(hook=None, *args, **kwargs):
			if hook == "crm_hidden_users":
				return [f"{__name__}._technical_users"]
			return original(hook, *args, **kwargs)

		hooks = patch.object(frappe, "get_hooks", side_effect=get_hooks)
		hooks.start()
		self.addCleanup(hooks.stop)
		if not frappe.db.exists("User", TECH):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": TECH,
					"first_name": "API: ERP",
					"send_welcome_email": 0,
					"roles": [{"role": "Sales User"}, {"role": "Pipeline Owner"}],
				}
			).insert(ignore_permissions=True)
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Hidden Users",
				"stages": [{"deal_status": "New"}, {"deal_status": "Won", "type": "Won"}],
				"members": [{"user": u, "role": "Member"} for u in SELLERS],
			}
		)["name"]
		# The app that owns the hidden user adds its membership directly (save_pipeline ignores hidden users)
		doc = frappe.get_doc("CRM Pipeline", self.pipeline)
		doc.append("members", {"user": TECH, "role": "Owner"})
		doc.save(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_hook_lists_hidden_users(self):
		self.assertEqual(hidden_users(), {TECH})

	def test_not_a_crm_user_but_name_still_resolves(self):
		_users, crm_users = get_users()
		self.assertNotIn(TECH, [u.name for u in crm_users])
		all_users, crm_users = get_users(include_all=True)
		self.assertIn(TECH, [u.name for u in all_users])
		self.assertNotIn(TECH, [u.name for u in crm_users])

	def test_out_of_pipeline_screens(self):
		self.assertNotIn(TECH, [u["name"] for u in get_pipeline_users()["users"]])
		self.assertNotIn(TECH, [m["user"] for m in get_pipeline_config(self.pipeline)["members"]])

	def test_saving_members_keeps_hidden_membership(self):
		save_pipeline({"name": self.pipeline, "members": [{"user": SELLERS[0], "role": "Member"}]})
		rows = frappe.get_all("CRM Pipeline Member", {"parent": self.pipeline}, ["user", "role"])
		self.assertEqual({(r.user, r.role) for r in rows}, {(SELLERS[0], "Member"), (TECH, "Owner")})
		# Sending a hidden user from outside does not change its row either
		save_pipeline({"name": self.pipeline, "members": [{"user": TECH, "role": "Member"}]})
		rows = frappe.get_all("CRM Pipeline Member", {"parent": self.pipeline}, ["user", "role"])
		self.assertEqual({(r.user, r.role) for r in rows}, {(TECH, "Owner")})

	def test_hidden_user_keeps_its_access(self):
		# Still an Owner of the pipeline for the permissions: it sees every card of it
		self.assertTrue(
			frappe.db.exists("CRM Pipeline Member", {"parent": self.pipeline, "user": TECH, "role": "Owner"})
		)

	def test_distribution_never_picks_hidden_owner(self):
		# A rule pointing at the hidden user is skipped, and the fallback owner is hidden too: nobody is picked
		save_pipeline(
			{
				"name": self.pipeline,
				"distribution": {
					"mode": "rules",
					"rules": [{"field": "source", "value": "X", "user": TECH}],
					"fallback": "owner",
				},
			}
		)
		self.assertIsNone(pick_salesperson(self.pipeline, {"source": "X"}))
		# Round robin over a list that includes the hidden user skips it
		save_pipeline(
			{"name": self.pipeline, "distribution": {"mode": "round_robin", "round_robin_users": [TECH, SELLERS[1]]}}
		)
		self.assertEqual({pick_salesperson(self.pipeline, {}) for _ in range(3)}, {SELLERS[1]})
