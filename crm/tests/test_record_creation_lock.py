# Copyright (c) 2026, CredTech Digital and Contributors
# See license.txt

import frappe

from crm.tests import CRMTestCase as FrappeTestCase
from crm.utils.locks import _lock_name, acquire_record_creation_lock


def lock_holder():
	return frappe.db.sql("select is_used_lock(%s)", (_lock_name(),))[0][0]


class TestRecordCreationLock(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_lock_is_held_until_the_transaction_ends(self):
		acquire_record_creation_lock()
		acquire_record_creation_lock()  # second call in the same transaction is a no-op
		self.assertEqual(lock_holder(), frappe.db.sql("select connection_id()")[0][0])
		frappe.db.rollback()
		self.assertIsNone(lock_holder())
		self.assertFalse(frappe.flags.get("crm_record_creation_lock"))

	def test_conversion_takes_the_lock(self):
		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal
		from crm.tests import default_test_pipeline

		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Lock", "organization": "Lock Org"})
		lead.insert(ignore_permissions=True)
		convert_to_deal(lead.name, deal={"pipeline": default_test_pipeline()})
		self.assertTrue(frappe.flags.get("crm_record_creation_lock"))
		self.assertIsNotNone(lock_holder())
