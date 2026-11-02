"""Payments, promise and agreement schedule per title (credtech#315)."""

import frappe
from frappe.utils import add_days, flt, nowdate

from crm.api import collection
from crm.api.pipeline import save_pipeline
from crm.fcrm.doctype.crm_deal_title.crm_deal_title import balance_of
from crm.tests import CRMTestCase as FrappeTestCase


class TestCollection(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{"pipeline_name": "Collection Test", "stages": [{"deal_status": "Backlog", "type": "Open"}]}
		)["name"]
		self.deal = self.new_deal()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def new_deal(self, *amounts):
		amounts = amounts or (1000, 500)
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"pipeline": self.pipeline,
				"titles": [
					{
						"title_number": f"T{i}",
						"due_date": add_days(nowdate(), -30),
						"original_amount": amount,
					}
					for i, amount in enumerate(amounts, start=1)
				],
			}
		).insert()
		return deal.name

	def doc(self):
		return frappe.get_doc("CRM Deal", self.deal)

	def title(self, index=0):
		return self.doc().titles[index]

	def comments(self):
		return frappe.get_all(
			"Comment", {"reference_doctype": "CRM Deal", "reference_name": self.deal}, pluck="content"
		)

	def pay(self, amount, index=0, **kwargs):
		return collection.record_payment(self.deal, self.title(index).name, amount, **kwargs)

	def plan(self, *amounts, start=10):
		return [{"due_date": add_days(nowdate(), start + 30 * i), "amount": a} for i, a in enumerate(amounts)]

	# ---- balance and payments

	def test_balance_starts_as_the_original_amount(self):
		self.assertEqual(balance_of(self.title()), 1000)
		self.assertEqual(self.doc().deal_value, 1500)

	def test_partial_payment_lowers_the_balance_and_keeps_the_history(self):
		result = self.pay(300, note="PIX")
		self.assertEqual((result["balance"], result["paid"]), (700, 300))
		self.assertFalse(result["title_paid"])
		self.assertFalse(result["all_paid"])
		doc = self.doc()
		self.assertEqual(doc.deal_value, 1200)
		self.assertEqual(doc.titles[0].original_amount, 1000)
		entry = doc.payments[0]
		self.assertEqual((entry.title, entry.amount, entry.balance_after), (doc.titles[0].name, 300, 700))
		self.assertEqual((entry.note, entry.registered_by), ("PIX", "Administrator"))
		self.assertTrue(any("700" in c and "T1" in c for c in self.comments()))

	def test_paid_title_keeps_a_zero_balance(self):
		self.pay(400)
		result = self.pay(600)
		self.assertEqual(result["balance"], 0)
		self.assertTrue(result["title_paid"])
		self.assertFalse(result["all_paid"])
		doc = self.doc()
		doc.save()  # saving again must not bring the original amount back
		doc.reload()
		self.assertEqual(balance_of(doc.titles[0]), 0)
		self.assertEqual(doc.deal_value, 500)
		self.assertEqual(flt(doc.titles[0].paid_amount), 1000)

	def test_all_paid_is_reported_but_the_card_is_not_closed(self):
		self.pay(1000)
		result = self.pay(500, index=1)
		self.assertTrue(result["all_paid"])
		doc = self.doc()
		self.assertEqual((doc.outcome, doc.deal_value), ("In progress", 0))

	def test_payment_rules(self):
		for amount in (0, -5):
			with self.assertRaises(frappe.ValidationError):
				self.pay(amount)
		with self.assertRaises(frappe.ValidationError):
			self.pay(1000.01)
		with self.assertRaises(frappe.ValidationError):
			self.pay(10, paid_on=add_days(nowdate(), 1))
		self.assertFalse(self.doc().payments)
		self.assertEqual(balance_of(self.title()), 1000)

	def test_reverse_payment_gives_the_amount_back(self):
		self.pay(1000)
		doc = self.doc()
		result = collection.reverse_payment(self.deal, doc.payments[0].name)
		self.assertEqual((result["balance"], result["paid"]), (1000, 0))
		doc = self.doc()
		self.assertFalse(doc.payments)
		self.assertEqual((balance_of(doc.titles[0]), doc.deal_value), (1000, 1500))

	def test_title_with_the_registry_warns_but_nothing_is_withdrawn(self):
		doc = self.doc()
		doc.titles[0].sent_at = frappe.utils.now_datetime()
		doc.titles[0].protest_status = "CONFIRMADO"
		doc.save()
		result = self.pay(100)
		self.assertIn("CONFIRMADO", result["warning"])
		self.assertEqual(self.title().protest_status, "CONFIRMADO")
		self.assertIsNone(self.pay(100, index=1)["warning"])

	def test_only_who_can_write_the_card_registers_payments(self):
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			self.pay(10)

	# ---- promise

	def test_promise_is_set_and_cleared(self):
		date = add_days(nowdate(), 5)
		collection.set_promise(self.deal, self.title().name, date)
		row = self.title()
		self.assertEqual((str(row.promise_date), row.promise_amount), (date, 1000))
		collection.set_promise(self.deal, row.name, date, 400)
		self.assertEqual(self.title().promise_amount, 400)
		collection.set_promise(self.deal, row.name, None)
		row = self.title()
		self.assertFalse(row.promise_date)
		self.assertFalse(row.promise_amount)

	def test_promise_cannot_be_in_the_past(self):
		with self.assertRaises(frappe.ValidationError):
			collection.set_promise(self.deal, self.title().name, add_days(nowdate(), -1))

	# ---- balance adjustment

	def test_adjusting_the_balance_keeps_the_reason_in_the_history(self):
		collection.adjust_balance(self.deal, self.title().name, 1180.5, "interest until today")
		self.assertEqual(balance_of(self.title()), 1180.5)
		self.assertEqual(self.title().original_amount, 1000)
		self.assertTrue(any("1.180,50" in c or "1,180.50" in c for c in self.comments()))
		self.assertTrue(any("interest until today" in c for c in self.comments()))
		with self.assertRaises(frappe.ValidationError):
			collection.adjust_balance(self.deal, self.title().name, 0)

	# ---- agreement

	def test_suggested_plan_adds_up_to_the_balance(self):
		plan = collection.suggest_agreement(self.deal, self.title().name, 3, "2026-12-31")
		self.assertEqual([p["due_date"] for p in plan], ["2026-12-31", "2027-01-31", "2027-02-28"])
		self.assertEqual([p["amount"] for p in plan], [333.33, 333.33, 333.34])
		self.assertEqual(flt(sum(p["amount"] for p in plan), 2), 1000)

	def test_agreement_creates_the_schedule(self):
		result = collection.create_agreement(self.deal, self.title().name, self.plan(400, 600))
		self.assertEqual(result["balance"], 1000)
		doc = self.doc()
		self.assertEqual(
			[(i.number, i.amount, i.paid_on) for i in doc.installments], [(1, 400, None), (2, 600, None)]
		)
		self.assertTrue(all(i.title == doc.titles[0].name for i in doc.installments))
		self.assertTrue(any("T1" in c and "2" in c for c in self.comments()))

	def test_agreement_rules(self):
		name = self.title().name
		with self.assertRaises(frappe.ValidationError):
			collection.create_agreement(self.deal, name, [])
		with self.assertRaises(frappe.ValidationError):
			collection.create_agreement(self.deal, name, self.plan(400, 500))  # does not add up
		with self.assertRaises(frappe.ValidationError):
			collection.create_agreement(self.deal, name, self.plan(1000, start=-2))  # in the past
		with self.assertRaises(frappe.ValidationError):
			collection.create_agreement(self.deal, name, self.plan(1100, -100))
		self.assertFalse(self.doc().installments)
		collection.create_agreement(self.deal, name, self.plan(1000))
		with self.assertRaises(frappe.ValidationError):  # one agreement at a time
			collection.create_agreement(self.deal, name, self.plan(1000))
		with self.assertRaises(frappe.ValidationError):  # balance is frozen while the agreement runs
			collection.adjust_balance(self.deal, name, 900)

	def test_paying_an_installment_settles_it(self):
		name = self.title().name
		collection.create_agreement(self.deal, name, self.plan(400, 600))
		first = self.doc().installments[0]
		result = collection.record_payment(self.deal, name, installment=first.name)
		self.assertEqual(result["balance"], 600)
		doc = self.doc()
		self.assertEqual(str(doc.installments[0].paid_on), nowdate())
		self.assertEqual((doc.payments[0].installment, doc.payments[0].amount), (first.name, 400))
		with self.assertRaises(frappe.ValidationError):  # twice
			collection.record_payment(self.deal, name, installment=first.name)
		collection.reverse_payment(self.deal, doc.payments[0].name)
		doc = self.doc()
		self.assertFalse(doc.installments[0].paid_on)
		self.assertEqual(balance_of(doc.titles[0]), 1000)

	def test_cancel_keeps_the_paid_installments_and_numbering_goes_on(self):
		name = self.title().name
		collection.create_agreement(self.deal, name, self.plan(400, 300, 300))
		collection.record_payment(self.deal, name, installment=self.doc().installments[0].name)
		collection.cancel_agreement(self.deal, name)
		doc = self.doc()
		self.assertEqual([(i.number, bool(i.paid_on)) for i in doc.installments], [(1, True)])
		self.assertEqual(balance_of(doc.titles[0]), 600)
		with self.assertRaises(frappe.ValidationError):  # nothing left to cancel
			collection.cancel_agreement(self.deal, name)
		collection.create_agreement(self.deal, name, self.plan(600))
		self.assertEqual([i.number for i in self.doc().installments], [1, 2])

	def test_installments_of_other_titles_do_not_mix(self):
		first, second = (t.name for t in self.doc().titles)
		collection.create_agreement(self.deal, first, self.plan(1000))
		collection.create_agreement(self.deal, second, self.plan(250, 250, start=5))
		slot = next(i for i in self.doc().installments if i.title == first)
		with self.assertRaises(frappe.DoesNotExistError):
			collection.record_payment(self.deal, second, installment=slot.name)
