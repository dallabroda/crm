"""Card status In progress / Won / Lost, separate from the stage (credtech#315)."""

import frappe
from frappe.utils import nowdate

from crm.api.pipeline import save_pipeline
from crm.tests import CRMTestCase as FrappeTestCase


def lost_reason(name="Preço"):
	if not frappe.db.exists("CRM Lost Reason", name):
		frappe.get_doc({"doctype": "CRM Lost Reason", "lost_reason": name}).insert()
	return name


class TestDealOutcome(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Outcome Test",
				"stages": [
					{"deal_status": "Novo"},
					{"deal_status": "Negociando", "type": "Ongoing"},
					{"deal_status": "Fechado ganho", "type": "Won"},
					{"deal_status": "Fechado perdido", "type": "Lost"},
				],
			}
		)["name"]
		self.stages = {
			row.deal_status: row.name
			for row in frappe.get_all("CRM Deal Status", {"pipeline": self.pipeline}, ["name", "deal_status"])
		}

	def tearDown(self):
		frappe.db.rollback()

	def deal(self, **fields):
		return frappe.get_doc({"doctype": "CRM Deal", "pipeline": self.pipeline, **fields}).insert()

	def comments(self, deal):
		return frappe.get_all(
			"Comment", {"reference_doctype": "CRM Deal", "reference_name": deal.name}, pluck="content"
		)

	def test_new_card_is_in_progress(self):
		deal = self.deal()
		self.assertEqual(deal.outcome, "In progress")
		self.assertFalse(deal.closed_date)

	def test_won_keeps_the_stage_and_records_the_date(self):
		deal = self.deal(status=self.stages["Negociando"])
		deal.outcome = "Won"
		deal.save()
		deal.reload()
		self.assertEqual((deal.outcome, deal.status), ("Won", self.stages["Negociando"]))
		self.assertEqual(str(deal.closed_date), nowdate())
		self.assertIn("Card marked as won.", self.comments(deal))

	def test_lost_needs_a_reason(self):
		deal = self.deal()
		deal.outcome = "Lost"
		with self.assertRaises(frappe.ValidationError):
			deal.save()
		deal.reload()
		deal.outcome = "Lost"
		deal.lost_reason = lost_reason()
		deal.save()
		deal.reload()
		self.assertEqual(deal.outcome, "Lost")
		self.assertTrue(deal.closed_date)
		self.assertTrue(any("Preço" in comment for comment in self.comments(deal)))

	def test_reopen_clears_the_close(self):
		deal = self.deal()
		deal.update({"outcome": "Lost", "lost_reason": lost_reason()})
		deal.save()
		deal.outcome = "In progress"
		deal.save()
		deal.reload()
		self.assertEqual(deal.outcome, "In progress")
		self.assertFalse(deal.closed_date)
		self.assertFalse(deal.lost_reason)
		self.assertIn("Card reopened.", self.comments(deal))

	def test_older_funnels_won_and_lost_stages_close_and_reopen_the_card(self):
		deal = self.deal()
		deal.status = self.stages["Fechado ganho"]
		deal.save()
		deal.reload()
		self.assertEqual(deal.outcome, "Won")
		deal.status = self.stages["Novo"]
		deal.save()
		deal.reload()
		self.assertEqual(deal.outcome, "In progress")
		self.assertFalse(deal.closed_date)
		deal.update({"status": self.stages["Fechado perdido"], "lost_reason": lost_reason()})
		deal.save()
		deal.reload()
		self.assertEqual(deal.outcome, "Lost")
