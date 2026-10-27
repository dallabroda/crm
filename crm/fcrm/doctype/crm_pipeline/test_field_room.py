# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt

from unittest.mock import patch

import frappe

from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.tests import CRMTestCase as FrappeTestCase


class TestFieldRoom(FrappeTestCase):
	"""Cards run out of row size before the created-field limit: creating a field must say so clearly."""

	def tearDown(self) -> None:
		frappe.db.rollback()

	def test_field_cost_follows_the_column_type(self):
		self.assertEqual(field_catalog.field_cost("Data"), 562)
		self.assertEqual(field_catalog.field_cost("Select"), 562)
		self.assertEqual(field_catalog.field_cost("Link"), 562)
		self.assertEqual(field_catalog.field_cost("Int"), 4)
		self.assertEqual(field_catalog.field_cost("Check"), 1)
		self.assertEqual(field_catalog.field_cost("Date"), 3)
		self.assertEqual(field_catalog.field_cost("Currency"), 10)
		self.assertLess(field_catalog.field_cost("Attach"), 20)

	def test_row_size_counts_only_this_site(self):
		size = field_catalog.row_size()
		self.assertGreater(size, 1000)
		self.assertLess(size, field_catalog.ROW_SIZE_LIMIT)

	def test_room_by_type_text_runs_out_first(self):
		room = field_catalog.room_by_type()
		self.assertEqual(set(room), set(field_catalog.FIELD_TYPES))
		self.assertLessEqual(room["Data"], room["Int"])
		self.assertLessEqual(room["Int"], field_catalog.CREATED_FIELD_LIMIT)

	def test_create_field_without_room_is_refused_clearly(self):
		size = field_catalog.row_size()
		# leave room for a number but not for a text field
		limit = size + field_catalog.ROW_SIZE_MARGIN + 100
		with patch.object(field_catalog, "ROW_SIZE_LIMIT", limit):
			with self.assertRaises(field_catalog.NoRoomForFieldError):
				field_catalog.create_field("Observação longa", "Data")
			self.assertEqual(field_catalog.room_by_type()["Data"], 0)
			self.assertGreater(field_catalog.room_by_type()["Int"], 0)

	def test_row_size_error_after_alter_leaves_no_orphan_field(self):
		"""ALTER TABLE commits the Custom Field row before failing with 1118: it must be removed."""

		def fail_after_saving(doctype, df, ignore_validate=False):
			# what create_custom_field leaves behind when the ALTER is refused
			frappe.get_doc(
				{"doctype": "Custom Field", "dt": doctype, "fieldtype": df["fieldtype"], **df}
			).db_insert()
			frappe.db.commit()  # the implicit commit of ALTER TABLE: a rollback alone would not undo it
			raise frappe.db.OperationalError(1118, "Row size too large")

		with patch.object(field_catalog, "create_custom_field", side_effect=fail_after_saving):
			with self.assertRaises(field_catalog.NoRoomForFieldError):
				field_catalog.create_field("Campo que não cabe", "Data")
		self.assertFalse(
			frappe.db.exists("Custom Field", {"dt": field_catalog.DEAL, "fieldname": "ch_campo_que_nao_cabe"})
		)
