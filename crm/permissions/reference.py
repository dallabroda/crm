# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Notes and tasks belong to a card or a lead: whoever cannot see it does not see them (credtech#288).

Without these rules the Sales User role read, edited and deleted every note and task of the company
through the API, including the ones on cards of pipelines the user is not part of. A task stays
visible to the person it is assigned to. Notes and tasks not tied to a card or lead keep the role
permissions.
"""

import frappe

from crm.permissions.org_hierarchy import get_lead_permission_query_conditions
from crm.permissions.pipeline import deal_conditions, is_admin

PARENTS = ("CRM Deal", "CRM Lead")


def _visible_deals_sql(user: str) -> str | None:
	cond = deal_conditions(user)
	if cond is None:
		return None
	Deal = frappe.qb.DocType("CRM Deal")
	return frappe.qb.from_(Deal).select(Deal.name).where(cond).get_sql()


def _conditions(doctype: str, user: str | None) -> str:
	user = user or frappe.session.user
	if is_admin(user):
		return ""
	table = f"`tab{doctype}`"
	deals = _visible_deals_sql(user)
	leads = get_lead_permission_query_conditions(user)
	deal_rule = f"{table}.`reference_docname` in ({deals})" if deals else "1=1"
	lead_rule = (
		f"{table}.`reference_docname` in (select `tabCRM Lead`.`name` from `tabCRM Lead` where {leads})"
		if leads
		else "1=1"
	)
	rules = [
		f"ifnull({table}.`reference_doctype`, '') not in ('CRM Deal', 'CRM Lead')",
		f"({table}.`reference_doctype` = 'CRM Deal' and {deal_rule})",
		f"({table}.`reference_doctype` = 'CRM Lead' and {lead_rule})",
	]
	if doctype == "CRM Task":
		rules.append(f"{table}.`assigned_to` = {frappe.db.escape(user)}")
	return "(" + " or ".join(rules) + ")"


def get_note_permission_query_conditions(user=None):
	return _conditions("FCRM Note", user)


def get_task_permission_query_conditions(user=None):
	return _conditions("CRM Task", user)


def _has_permission(doc, user) -> bool:
	user = user or frappe.session.user
	if is_admin(user):
		return True
	parent, name = doc.get("reference_doctype"), doc.get("reference_docname")
	if parent not in PARENTS or not name or not frappe.db.exists(parent, name):
		return True
	if doc.doctype == "CRM Task" and doc.get("assigned_to") == user:
		return True
	# reading the card is enough to see, add, edit and remove its notes and tasks, as in the card screen
	return bool(frappe.has_permission(parent, "read", doc=name, user=user))


def has_note_permission(doc, ptype, user):
	return _has_permission(doc, user)


def has_task_permission(doc, ptype, user):
	return _has_permission(doc, user)
