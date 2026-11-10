"""Payments, promise and agreement schedule of a collection title (credtech#315).

The title is a row of the card and its open balance is `updated_amount`: it starts as the original amount, the analyst may
correct it, and every payment lowers it. A title is paid when its balance reaches 0. The system tells the analyst what
it sees (the title is already with the registry, every title of the card is paid) and the analyst decides: nothing here
withdraws a title from the registry or closes the card, because both can cost the client or change the case.
"""

import json

import frappe
from frappe import _
from frappe.utils import add_to_date, flt, fmt_money, getdate, nowdate

from crm.fcrm.doctype.crm_deal_title.crm_deal_title import balance_of

# CENPROT / registry statuses in which the title is (or may be) at the registry
WITH_REGISTRY = {
	"COLETADO",
	"GERADO",
	"AGENDADO",
	"ENVIADO",
	"CONFIRMADO",
	"DISTRIBUIDO",
	"INTIMADO",
	"PROTESTADO",
	"SUSPENSO",
	"SUSTADO",
}
MAX_INSTALLMENTS = 60
CENT = 0.005


def _load(deal: str, title: str):
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("write")
	row = next((t for t in doc.titles if t.name == title), None)
	if not row:
		frappe.throw(_("Title not found on this card."), frappe.DoesNotExistError)
	return doc, row


def _money(value) -> str:
	return fmt_money(flt(value, 2), currency="BRL")


def _registry_warning(row) -> str | None:
	status = (row.protest_status or "").strip().upper()
	if row.sent_at and status in WITH_REGISTRY:
		return _(
			"Title {0} is with the registry ({1}). Withdrawing or cancelling it is your decision and may have a cost."
		).format(row.title_number, status)
	return None


def _summary(doc, row, warning: str | None = None) -> dict:
	balance = balance_of(row)
	return {
		"balance": balance,
		"paid": flt(row.paid_amount),
		"title_paid": balance <= CENT,
		"all_paid": all(balance_of(t) <= CENT for t in doc.titles),
		"warning": warning,
	}


def _erp_locked(row) -> str | None:
	"""Name of the ERP that owns the balance of this title (a title synced from an ERP), else None. The custom field
	`erp_title_id` is added by cred_hub; without it no title is locked."""
	return (row.get("erp_source") or "ERP") if row.get("erp_title_id") else None


def _require_manual_balance(row) -> None:
	"""The ERP is the source of truth of the balance (credtech#367): payments, settlements and balance changes of its
	titles come from the synchronization, never by hand, so nothing is counted twice."""
	erp = _erp_locked(row)
	if erp:
		frappe.throw(
			_(
				"The balance of title {0} comes from {1}. Payments and settlements are registered by the ERP synchronization, not by hand."
			).format(row.title_number, erp),
			frappe.ValidationError,
		)


def _open_installments(doc, title: str) -> list:
	"""Installments still to be paid: neither paid nor cancelled."""
	return [i for i in doc.installments if i.title == title and not i.paid_on and not i.cancelled_on]


def _note(doc, text: str) -> None:
	doc.add_comment("Info", text)


@frappe.whitelist()
def record_payment(
	deal: str,
	title: str,
	amount: float | None = None,
	paid_on: str | None = None,
	installment: str | None = None,
	note: str | None = None,
) -> dict:
	"""Register a payment: the balance of the title falls by the amount. With `installment` the payment settles that
	installment of the agreement (its amount)."""
	doc, row = _load(deal, title)
	_require_manual_balance(row)
	balance = balance_of(row)
	slot = None
	if installment:
		slot = next((i for i in doc.installments if i.name == installment and i.title == title), None)
		if not slot:
			frappe.throw(_("Installment not found on this title."), frappe.DoesNotExistError)
		if slot.paid_on:
			frappe.throw(_("Installment {0} is already paid.").format(slot.number))
		if slot.cancelled_on:
			frappe.throw(_("Installment {0} was cancelled.").format(slot.number))
		amount = slot.amount
	amount = flt(amount, 2)
	paid_on = getdate(paid_on or nowdate())
	if amount <= 0:
		frappe.throw(_("The payment must be greater than zero."))
	if paid_on > getdate(nowdate()):
		frappe.throw(_("The payment date cannot be in the future."))
	if amount > balance + CENT:
		frappe.throw(
			_(
				"The payment ({0}) is higher than the balance of the title ({1}). Adjust the balance first if it is wrong."
			).format(_money(amount), _money(balance))
		)

	after = max(flt(balance - amount, 2), 0)
	doc.append(
		"payments",
		{
			"title": row.name,
			"paid_on": paid_on,
			"amount": amount,
			"balance_after": after,
			"installment": slot.name if slot else None,
			"note": (note or "").strip() or None,
			"registered_by": frappe.session.user,
		},
	)
	row.updated_amount = after
	row.paid_amount = flt(flt(row.paid_amount) + amount, 2)
	if slot:
		slot.paid_on = paid_on
	doc.save()
	_note(
		doc,
		_("Payment of {0} registered on title {1}. Balance: {2}.").format(
			_money(amount), row.title_number, _money(after)
		),
	)
	return _summary(doc, row, _registry_warning(row))


@frappe.whitelist()
def reverse_payment(deal: str, payment: str) -> dict:
	"""Undo a payment registered by mistake: the amount goes back to the balance and its installment reopens."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("write")
	entry = next((p for p in doc.payments if p.name == payment), None)
	if not entry:
		frappe.throw(_("Payment not found on this card."), frappe.DoesNotExistError)
	row = next((t for t in doc.titles if t.name == entry.title), None)
	if not row:
		frappe.throw(_("Title not found on this card."), frappe.DoesNotExistError)
	_require_manual_balance(row)
	back = flt(balance_of(row) + flt(entry.amount), 2)
	row.paid_amount = max(flt(flt(row.paid_amount) - flt(entry.amount), 2), 0)
	row.updated_amount = back
	if entry.installment:
		for slot in doc.installments:
			if slot.name == entry.installment:
				slot.paid_on = None
	doc.remove(entry)
	doc.save()
	_note(
		doc,
		_("Payment of {0} reversed on title {1}. Balance: {2}.").format(
			_money(entry.amount), row.title_number, _money(back)
		),
	)
	return _summary(doc, row)


@frappe.whitelist()
def set_promise(
	deal: str, title: str, promise_date: str | None = None, promise_amount: float | None = None
) -> dict:
	"""The debtor promised to pay on a date (an empty date clears the promise)."""
	doc, row = _load(deal, title)
	if not promise_date:
		row.promise_date = None
		row.promise_amount = 0
		text = _("Promise of payment cleared on title {0}.").format(row.title_number)
	else:
		date = getdate(promise_date)
		if date < getdate(nowdate()):
			frappe.throw(_("The promise date cannot be in the past."))
		amount = flt(promise_amount, 2) or balance_of(row)
		if amount <= 0:
			frappe.throw(_("The promised amount must be greater than zero."))
		row.promise_date = date
		row.promise_amount = amount
		text = _("Promise of {0} on {1} registered on title {2}.").format(
			_money(amount), frappe.utils.formatdate(date), row.title_number
		)
	doc.save()
	_note(doc, text)
	return _summary(doc, row)


@frappe.whitelist()
def adjust_balance(deal: str, title: str, balance: float, reason: str | None = None) -> dict:
	"""Correct the open balance (interest, discount). The change stays in the card history."""
	doc, row = _load(deal, title)
	_require_manual_balance(row)
	new = flt(balance, 2)
	if new <= 0:
		frappe.throw(_("The balance must be greater than zero. To settle the title, register a payment."))
	if _open_installments(doc, row.name):
		frappe.throw(
			_("This title has an agreement in progress. Cancel the agreement before changing the balance.")
		)
	old = balance_of(row)
	row.updated_amount = new
	doc.save()
	text = _("Balance of title {0} changed from {1} to {2}.").format(
		row.title_number, _money(old), _money(new)
	)
	if reason and reason.strip():
		text += " " + _("Reason: {0}").format(reason.strip())
	_note(doc, text)
	warning = _registry_warning(row)
	if warning:
		warning += " " + _("The registry keeps the amount it received.")
	return _summary(doc, row, warning)


@frappe.whitelist()
def create_agreement(deal: str, title: str, installments: str | list) -> dict:
	"""Agreement as a schedule of installments (due date and amount of each). It must add up to the balance of the
	title: for a discount or interest, adjust the balance first."""
	doc, row = _load(deal, title)
	plan = json.loads(installments) if isinstance(installments, str) else installments
	if not plan:
		frappe.throw(_("The agreement needs at least one installment."))
	if len(plan) > MAX_INSTALLMENTS:
		frappe.throw(_("An agreement can have up to {0} installments.").format(MAX_INSTALLMENTS))
	if _open_installments(doc, row.name):
		frappe.throw(_("This title already has an agreement in progress. Cancel it before creating another."))
	today = getdate(nowdate())
	rows = []
	for item in plan:
		if not item.get("due_date"):
			frappe.throw(_("Every installment needs a due date."))
		due, amount = getdate(item["due_date"]), flt(item.get("amount"), 2)
		if due < today:
			frappe.throw(_("An installment cannot be due in the past."))
		if amount <= 0:
			frappe.throw(_("Every installment must be greater than zero."))
		rows.append((due, amount))
	rows.sort(key=lambda r: r[0])
	total, balance = flt(sum(a for _d, a in rows), 2), balance_of(row)
	if abs(total - balance) > CENT:
		frappe.throw(
			_(
				"The installments add up to {0} but the balance of the title is {1}. For a discount or interest, adjust the balance first."
			).format(_money(total), _money(balance))
		)
	start = max([i.number or 0 for i in doc.installments if i.title == row.name] or [0])
	for offset, (due, amount) in enumerate(rows, start=1):
		doc.append(
			"installments", {"title": row.name, "number": start + offset, "due_date": due, "amount": amount}
		)
	doc.save()
	_note(
		doc,
		_("Agreement of {0} in {1} installment(s) created on title {2}: first due on {3}.").format(
			_money(total), len(rows), row.title_number, frappe.utils.formatdate(rows[0][0])
		),
	)
	return _summary(doc, row, _registry_warning(row))


@frappe.whitelist()
def cancel_agreement(deal: str, title: str) -> dict:
	"""Cancel the installments still open: they stay in the history as cancelled (counting neither as paid nor as
	open), like the ones already paid."""
	doc, row = _load(deal, title)
	open_ones = _open_installments(doc, row.name)
	if not open_ones:
		frappe.throw(_("This title has no agreement in progress."))
	for slot in open_ones:
		slot.cancelled_on = getdate(nowdate())
	doc.save()
	_note(doc, _("Agreement cancelled on title {0}.").format(row.title_number))
	return _summary(doc, row)


@frappe.whitelist()
def suggest_agreement(deal: str, title: str, count: int, first_due: str) -> list[dict]:
	"""Equal monthly installments adding up to the balance (the last one takes the cents): the starting point the
	analyst edits before saving."""
	_doc, row = _load(deal, title)
	count = int(count)
	if not 1 <= count <= MAX_INSTALLMENTS:
		frappe.throw(_("An agreement can have from 1 to {0} installments.").format(MAX_INSTALLMENTS))
	balance = balance_of(row)
	share = flt(balance / count, 2)
	plan = [
		{"due_date": str(getdate(add_to_date(first_due, months=i))), "amount": share} for i in range(count)
	]
	plan[-1]["amount"] = flt(balance - share * (count - 1), 2)
	return plan
