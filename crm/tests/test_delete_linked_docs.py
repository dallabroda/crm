from unittest.mock import patch

import frappe

from crm.api.doc import get_linked_docs_of_document, remove_linked_doc_reference
from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal
from crm.tests import CRMTestCase as FrappeTestCase


class TestDeleteLinkedDocs(FrappeTestCase):
	"""Deleting an organization goes through "Delete or unlink linked documents": both buttons must work
	for a deal linked by its `organization` field, and failures must reach the user."""

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _org_with_deal_and_task(self, name):
		deal = create_test_deal(organization=name, status="Qualification")
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Call back",
				"status": "Todo",
				"reference_doctype": "CRM Deal",
				"reference_docname": deal.name,
			}
		).insert()
		return deal.organization, deal, task

	def _linked_items(self, org):
		return [
			{"doctype": d["reference_doctype"], "docname": d["reference_docname"]}
			for d in get_linked_docs_of_document("CRM Organization", org)
		]

	def test_unlink_all_clears_the_deal_organization(self):
		org, deal, task = self._org_with_deal_and_task("Unlink Test Org")
		remove_linked_doc_reference(
			self._linked_items(org), delete=False, doctype="CRM Organization", docname=org
		)

		self.assertIsNone(frappe.db.get_value("CRM Deal", deal.name, "organization"))
		self.assertTrue(frappe.db.exists("CRM Task", task.name))
		self.assertEqual(get_linked_docs_of_document("CRM Organization", org), [])
		frappe.delete_doc("CRM Organization", org)
		self.assertFalse(frappe.db.exists("CRM Organization", org))

	def test_delete_all_removes_the_deal_with_its_task(self):
		org, deal, task = self._org_with_deal_and_task("Delete Test Org")
		remove_linked_doc_reference(
			self._linked_items(org), delete=True, doctype="CRM Organization", docname=org
		)

		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))
		self.assertFalse(frappe.db.exists("CRM Task", task.name))
		frappe.delete_doc("CRM Organization", org)
		self.assertFalse(frappe.db.exists("CRM Organization", org))

	def test_delete_all_removes_an_address_the_organization_points_to(self):
		"""Production bug (29/10, credtech#260): an organization created from a CNPJ points to its Receita address,
		which links back to it; "Delete all" failed on the address."""
		org = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Receita Test Org"}
		).insert()
		address = frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": "Receita Test Org (Receita)",
				"address_type": "Office",
				"address_line1": "Rua A, 1",
				"city": "Florianópolis",
				"country": "Brazil",
				"links": [{"link_doctype": "CRM Organization", "link_name": org.name}],
			}
		).insert()
		org.db_set("address", address.name)

		remove_linked_doc_reference(
			self._linked_items(org.name), delete=True, doctype="CRM Organization", docname=org.name
		)

		self.assertFalse(frappe.db.exists("Address", address.name))
		frappe.delete_doc("CRM Organization", org.name)
		self.assertFalse(frappe.db.exists("CRM Organization", org.name))

	def test_failure_is_reported_instead_of_success(self):
		org, deal, _task = self._org_with_deal_and_task("Denied Test Org")
		items = self._linked_items(org)
		frappe.set_user("Guest")

		with self.assertRaises(frappe.ValidationError):
			remove_linked_doc_reference(items, delete=True, doctype="CRM Organization", docname=org)

		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("CRM Deal", deal.name))

	def test_history_record_stays_and_only_loses_the_link(self):
		# a record kept for history (here a note, standing in for the cred_hub lead log) is not offered for
		# deletion and does not block deleting the card
		org, deal, task = self._org_with_deal_and_task("Kept Test Org")
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "History",
				"reference_doctype": "CRM Deal",
				"reference_docname": deal.name,
			}
		).insert()
		with patch("crm.api.doc.kept_doctypes", return_value={"FCRM Note"}):
			offered = [d["reference_doctype"] for d in get_linked_docs_of_document("CRM Deal", deal.name)]
			self.assertNotIn("FCRM Note", offered)
			remove_linked_doc_reference(
				self._linked_items(org), delete=True, doctype="CRM Organization", docname=org
			)

		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))
		self.assertFalse(frappe.db.exists("CRM Task", task.name))
		kept = frappe.db.get_value("FCRM Note", note.name, ["reference_doctype", "reference_docname"])
		self.assertEqual(tuple(kept), (None, None))

	def test_lead_log_does_not_block_a_sales_manager(self):
		"""Production bug (27/10): a card that came from a site lead has a Cred Hub Lead Event pointing to it;
		"Delete all" on its organization failed for a Sales Manager, who cannot change those records."""
		if not frappe.db.exists("DocType", "Cred Hub Lead Event"):
			self.skipTest("cred_hub is not installed")
		org, deal, _task = self._org_with_deal_and_task("Lead Log Test Org")
		event = frappe.get_doc(
			{
				"doctype": "Cred Hub Lead Event",
				"source": "site",
				"status": "Created",
				"card_doctype": "CRM Deal",
				"card_name": deal.name,
			}
		).insert(ignore_permissions=True)
		manager = "crm.manager@example.com"
		self.assertNotIn("System Manager", frappe.get_roles(manager))

		frappe.set_user(manager)
		remove_linked_doc_reference(
			self._linked_items(org), delete=True, doctype="CRM Organization", docname=org
		)
		frappe.delete_doc("CRM Organization", org)

		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))
		self.assertFalse(frappe.db.exists("CRM Organization", org))
		# the log stays for the lead sources screen, without the deleted card
		self.assertEqual(frappe.db.get_value("Cred Hub Lead Event", event.name, "card_name"), None)

	def test_deleting_the_card_itself_with_a_lead_log(self):
		if not frappe.db.exists("DocType", "Cred Hub Lead Event"):
			self.skipTest("cred_hub is not installed")
		_org, deal, _task = self._org_with_deal_and_task("Card Log Test Org")
		frappe.get_doc(
			{
				"doctype": "Cred Hub Lead Event",
				"status": "Created",
				"card_doctype": "CRM Deal",
				"card_name": deal.name,
			}
		).insert(ignore_permissions=True)
		frappe.set_user("crm.manager@example.com")
		items = [
			{"doctype": d["reference_doctype"], "docname": d["reference_docname"]}
			for d in get_linked_docs_of_document("CRM Deal", deal.name)
		]
		self.assertNotIn("Cred Hub Lead Event", [i["doctype"] for i in items])
		remove_linked_doc_reference(items, delete=True, doctype="CRM Deal", docname=deal.name)
		frappe.delete_doc("CRM Deal", deal.name)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))

	def test_notification_to_someone_else_does_not_block_the_delete(self):
		"""A card assigned to a salesperson has a notification only that salesperson can see; a manager
		deleting the card must not be blocked by it."""
		_org, deal, _task = self._org_with_deal_and_task("Notified Card Test Org")
		frappe.get_doc(
			{
				"doctype": "CRM Notification",
				"from_user": "Administrator",
				"to_user": "crm.user1@example.com",
				"type": "Assignment",
				"notification_type_doctype": "CRM Deal",
				"notification_type_doc": deal.name,
				"reference_doctype": "CRM Deal",
				"reference_name": deal.name,
			}
		).insert(ignore_permissions=True)
		frappe.set_user("crm.manager@example.com")
		items = [
			{"doctype": d["reference_doctype"], "docname": d["reference_docname"]}
			for d in get_linked_docs_of_document("CRM Deal", deal.name)
		]
		remove_linked_doc_reference(items, delete=True, doctype="CRM Deal", docname=deal.name)
		frappe.delete_doc("CRM Deal", deal.name)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("CRM Deal", deal.name))
		self.assertFalse(frappe.db.exists("CRM Notification", {"reference_name": deal.name}))
