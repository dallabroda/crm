# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

"""Sandbox records of the HubTech API run no automation, ERP, assignment or notification side effect (crm.sandbox)."""

from unittest.mock import patch

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.model.document import Document

from crm import sandbox
from crm.api.pipeline import save_pipeline
from crm.automation import events
from crm.tests import CRMTestCase as FrappeTestCase

PIPELINE_NAME = "Sandbox guard test"


class TestSandboxGuards(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		# Without cred_hub the column does not exist: the test creates it (and removes only what it created)
		cls.created_fields = []
		for doctype in ("CRM Pipeline", *sandbox.STAMPED):
			if not sandbox.has_flag(doctype):
				create_custom_fields(
					{
						doctype: [
							{
								"fieldname": sandbox.FLAG,
								"fieldtype": "Check",
								"label": "API Sandbox",
								"hidden": 1,
							}
						]
					}
				)
				cls.created_fields.append(f"{doctype}-{sandbox.FLAG}")
		cls.sandbox_pipeline = cls.make_pipeline()
		cls.real_pipeline = cls.make_pipeline()
		cls.sandbox_card = cls.make_card(cls.sandbox_pipeline)
		cls.real_card = cls.make_card(cls.real_pipeline)
		# flagged after the card exists: in cred_hub only a test key creates cards in the Sandbox pipeline
		frappe.db.set_value(
			"CRM Pipeline", cls.sandbox_pipeline["name"], sandbox.FLAG, 1, update_modified=False
		)
		frappe.local.credhub_sandbox_pipeline = None
		frappe.db.commit()  # nosemgrep: fixtures shared by the tests

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for pipeline in (cls.sandbox_pipeline, cls.real_pipeline):
			for card in frappe.get_all("CRM Deal", {"pipeline": pipeline["name"]}, pluck="name"):
				frappe.db.delete("ToDo", {"reference_type": "CRM Deal", "reference_name": card})
				frappe.delete_doc("CRM Deal", card, force=True, ignore_permissions=True)
			frappe.db.set_value("CRM Pipeline", pipeline["name"], sandbox.FLAG, 0, update_modified=False)
			frappe.delete_doc("CRM Pipeline", pipeline["name"], force=True, ignore_permissions=True)
		for name in cls.created_fields:
			frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
		frappe.local.credhub_sandbox_pipeline = None
		frappe.db.commit()  # nosemgrep: fixtures commit, so clean up explicitly
		super().tearDownClass()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.local.crm_sandbox_records = {}

	def tearDown(self):
		frappe.db.rollback()
		frappe.local.crm_sandbox_records = {}

	@staticmethod
	def make_pipeline():
		return save_pipeline(
			{
				"pipeline_name": PIPELINE_NAME,
				"stages": [
					{"deal_status": "Novo", "type": "Open"},
					{"deal_status": "Andamento", "type": "Ongoing"},
					{"deal_status": "Ganho", "type": "Won"},
				],
			}
		)

	@staticmethod
	def make_card(pipeline):
		return (
			frappe.get_doc(
				{
					"doctype": "CRM Deal",
					"pipeline": pipeline["name"],
					"status": pipeline["stages"][0]["name"],
					"deal_owner": "Administrator",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def card(self, name):
		return frappe.get_doc("CRM Deal", name)

	# ---------- Detection ----------

	def test_detects_sandbox_cards_records_and_what_points_at_them(self):
		self.assertTrue(sandbox.is_sandbox(self.card(self.sandbox_card)))
		self.assertFalse(sandbox.is_sandbox(self.card(self.real_card)))
		self.assertTrue(sandbox.is_sandbox_record("CRM Deal", self.sandbox_card))
		self.assertFalse(sandbox.is_sandbox_record("CRM Deal", self.real_card))
		self.assertTrue(sandbox.is_sandbox({"doctype": "Contact", sandbox.FLAG: 1}))
		self.assertFalse(sandbox.is_sandbox({"doctype": "Contact", sandbox.FLAG: 0}))
		self.assertTrue(
			sandbox.is_sandbox({"doctype": "CRM Lead", "pipeline": self.sandbox_pipeline["name"]})
		)
		for doctype, (kind, ref) in sandbox.REFERENCES.items():
			self.assertTrue(
				sandbox.is_sandbox({"doctype": doctype, kind: "CRM Deal", ref: self.sandbox_card}), doctype
			)
			self.assertFalse(
				sandbox.is_sandbox({"doctype": doctype, kind: "CRM Deal", ref: self.real_card}), doctype
			)
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "n",
				"reference_doctype": "CRM Deal",
				"reference_docname": self.sandbox_card,
			}
		).insert(ignore_permissions=True)
		self.assertTrue(sandbox.is_sandbox_record("FCRM Note", note.name))
		# a file on a note of a Sandbox card is sandbox too
		self.assertTrue(
			sandbox.is_sandbox(
				{"doctype": "File", "attached_to_doctype": "FCRM Note", "attached_to_name": note.name}
			)
		)
		self.assertFalse(sandbox.is_sandbox_record("CRM Deal", "missing-card"))
		self.assertFalse(sandbox.is_sandbox_record("User", "Administrator"))

	# ---------- Automation flows ----------

	def test_crm_events_are_not_emitted_for_sandbox_cards(self):
		for name, expected in ((self.sandbox_card, 0), (self.real_card, 2)):
			card = self.card(name)
			card.status = (
				self.sandbox_pipeline["stages"][2]["name"]
				if name == self.sandbox_card
				else (self.real_pipeline["stages"][2]["name"])
			)
			with (
				patch.object(events, "_enabled", return_value=True),
				patch.object(events, "emit") as emit,
				patch.object(card, "has_value_changed", return_value=True),
				patch.object(card, "get_doc_before_save", return_value=None),
			):
				events.on_deal_update(card)
				events.on_lead_update(
					frappe._dict(
						doctype="CRM Lead",
						pipeline=card.pipeline,
						status="Qualified",
						name="x",
						has_value_changed=lambda f: True,
					)
				)
				events.emit_lead_converted(frappe._dict(doctype="CRM Lead", name="x"), name)
				events.on_communication(
					frappe._dict(
						doctype="Communication",
						name="c",
						reference_doctype="CRM Deal",
						reference_name=name,
						communication_type="Communication",
						sent_or_received="Sent",
						message_id="<m@x>",
					)
				)
				events.on_whatsapp_message(
					frappe._dict(
						doctype="WhatsApp Message",
						name="w",
						reference_doctype="CRM Deal",
						reference_name=name,
						type="Outgoing",
						message_id="wamid",
					)
				)
			if expected:
				self.assertGreater(emit.call_count, expected)
			else:
				emit.assert_not_called()

	def test_overdue_sweep_skips_sandbox_tasks(self):
		tasks = {}
		for name in (self.sandbox_card, self.real_card):
			tasks[name] = frappe.get_doc(
				{
					"doctype": "CRM Task",
					"title": "t",
					"reference_doctype": "CRM Deal",
					"reference_docname": name,
				}
			).insert(ignore_permissions=True)
		with patch.object(events, "emit") as emit:
			for task in tasks.values():
				events._emit_overdue_task(
					frappe._dict(
						name=task.name,
						reference_doctype="CRM Deal",
						reference_docname=task.reference_docname,
						due_date=None,
					)
				)
		self.assertEqual(emit.call_count, 1)
		self.assertEqual(emit.call_args.kwargs["payload"]["task"], tasks[self.real_card].name)

	def test_flows_queued_for_sandbox_records_are_skipped(self):
		self.assertIn(
			"crm.sandbox.skip_sandbox_trigger",
			frappe.get_hooks("doc_events").get("Automation Trigger Queue", {}).get("before_insert", []),
		)
		for name, expected in ((self.sandbox_card, "Skipped"), (self.real_card, "Pending")):
			row = frappe.new_doc("Automation Trigger Queue")
			row.update({"ref_doctype": "CRM Deal", "ref_name": name, "status": "Pending"})
			row.run_method("before_insert")
			self.assertEqual(row.status, expected)
		row = frappe.new_doc("Automation Trigger Queue")
		row.update({"ref_doctype": "CRM Deal", "ref_name": self.sandbox_card, "status": "Scheduled"})
		sandbox.skip_sandbox_trigger(row)
		self.assertEqual(row.status, "Skipped")

	# ---------- Frappe notifications and webhooks ----------

	def test_notifications_and_webhooks_do_not_fire_for_sandbox_records(self):
		for name, fires in ((self.sandbox_card, False), (self.real_card, True)):
			card = self.card(name)
			self.assertIsInstance(card, sandbox.SandboxDocument)
			with patch.object(Document, "run_notifications") as base:
				card.run_notifications("on_update")
			self.assertEqual(base.called, fires)
			other = frappe._dict(name="other")
			frappe.local._webhook_queue = [
				frappe._dict(doc=card, webhook=frappe._dict(name="w")),
				frappe._dict(doc=other, webhook=frappe._dict(name="w")),
			]
			try:
				card.run_method("onload")
				queued = [execution.doc for execution in frappe.local._webhook_queue]
			finally:
				frappe.local._webhook_queue = []
			self.assertEqual(card in queued, fires)
			self.assertIn(other, queued)
		for doctype in sandbox.GUARDED_DOCTYPES:
			self.assertIn(
				"crm.sandbox.SandboxDocument", frappe.get_hooks("extend_doctype_class").get(doctype, [])
			)

	# ---------- Assignment, distribution and CRM notifications ----------

	def test_assignment_rules_skip_sandbox_records(self):
		rule = frappe.new_doc("Assignment Rule")
		with (
			patch.object(type(rule), "do_assignment", create=True) as assign,
			patch.object(type(rule), "safe_eval", return_value=True),
		):
			self.assertFalse(rule.apply_assign(self.card(self.sandbox_card).as_dict()))
			assign.assert_not_called()
			rule.apply_assign(self.card(self.real_card).as_dict())
			assign.assert_called_once()

	def test_sandbox_entries_are_not_distributed(self):
		from crm.fcrm.doctype.crm_lead import crm_lead

		for pipeline, distributed in ((self.sandbox_pipeline, False), (self.real_pipeline, True)):
			lead = frappe.new_doc("CRM Lead")
			lead.update({"first_name": "Ana", "pipeline": pipeline["name"]})
			with (
				patch.object(crm_lead, "open_card_of", return_value=None),
				patch.object(crm_lead, "pick_salesperson", return_value="Administrator") as pick,
				patch.object(crm_lead, "convert_to_deal") as convert,
			):
				lead.convert_into_pipeline()
			self.assertEqual(pick.called, distributed)
			self.assertEqual(
				convert.call_args.kwargs["deal"]["deal_owner"], "Administrator" if distributed else None
			)

	def test_nobody_is_notified_about_sandbox_records(self):
		from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

		for name, notified in ((self.sandbox_card, False), (self.real_card, True)):
			values = {
				"owner": "Administrator",
				"assigned_to": "crm.user1@example.com",
				"notification_type": "Assignment",
				"message": f"sandbox test {name}",
				"notification_text": "t",
				"reference_doctype": "CRM Deal",
				"reference_docname": name,
				"redirect_to_doctype": "CRM Deal",
				"redirect_to_docname": name,
			}
			notify_user(values)
			self.assertEqual(
				bool(frappe.db.exists("CRM Notification", {"message": values["message"]})), notified
			)
		# a mention in a comment of a Sandbox card points at the comment
		comment = frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": "CRM Deal",
				"reference_name": self.sandbox_card,
				"content": "oi",
			}
		).insert(ignore_permissions=True)
		notify_user(
			{
				"owner": "Administrator",
				"assigned_to": "crm.user1@example.com",
				"notification_type": "Mention",
				"message": "sandbox mention",
				"reference_doctype": "Comment",
				"reference_docname": comment.name,
			}
		)
		self.assertFalse(frappe.db.exists("CRM Notification", {"message": "sandbox mention"}))

	# ---------- ERPNext and enrichment ----------

	def test_sandbox_cards_never_reach_erpnext(self):
		from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings as erp

		settings = frappe._dict(
			enabled=1, create_customer_on_status_change=1, deal_status=None, is_erpnext_in_different_site=0
		)
		for name, synced in ((self.sandbox_card, False), (self.real_card, True)):
			card = self.card(name)
			settings.deal_status = card.status
			with (
				patch.object(erp.frappe, "get_single", return_value=settings),
				patch.object(erp, "create_customer_from_deal") as create,
				patch.object(erp, "get_local_customer", return_value=None),
			):
				erp.create_customer_in_erpnext(card, "on_update")
				erp.check_customer_for_deal(name)
			self.assertEqual(create.call_count, 2 if synced else 0)

	def test_sandbox_records_are_not_enriched(self):
		from crm.domain_enrichment import tasks

		for name, enriched in ((self.sandbox_card, False), (self.real_card, True)):
			card = self.card(name)
			card.website = "https://example.com"
			with (
				patch.object(tasks, "auto_enrich_enabled_for", return_value=True),
				patch.object(tasks, "enqueue_enrichment") as enqueue,
			):
				tasks.auto_enrich_on_create(card)
			self.assertEqual(enqueue.called, enriched)
