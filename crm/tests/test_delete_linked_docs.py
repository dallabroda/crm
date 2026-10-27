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

	def test_failure_is_reported_instead_of_success(self):
		org, deal, _task = self._org_with_deal_and_task("Denied Test Org")
		items = self._linked_items(org)
		frappe.set_user("Guest")

		with self.assertRaises(frappe.ValidationError):
			remove_linked_doc_reference(items, delete=True, doctype="CRM Organization", docname=org)

		frappe.set_user("Administrator")
		self.assertTrue(frappe.db.exists("CRM Deal", deal.name))
