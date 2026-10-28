# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Second organization of a card and whose contacts the card shows (dynamic forms phase 4, credtech#195).

A card has its organization (`organization`, the main one: title, search, distribution) and, in any funnel, an
optional `second_organization` (e.g. the debtor of a receivable). The funnel may name it (`second_organization_label`,
e.g. "Debtor"). With two organizations, `contacts_from` says whose contacts the card shows (owner decisions 1 and 2
of 28/10/2026): the people linked to each organization and the phone and e-mail of its Receita Federal record.
"""

import frappe
from frappe import _

FIRST, SECOND, BOTH = "Organization", "Second organization", "Both"
CONTACTS_LIMIT = 20


def second_organization_label(pipeline: str | None) -> str:
	label = frappe.db.get_value("CRM Pipeline", pipeline, "second_organization_label") if pipeline else None
	return label or _("Second organization")


def before_validate(doc, method=None):
	"""CRM Deal: the second organization is another company; a new card takes the funnel's default."""
	if doc.second_organization and doc.second_organization == doc.organization:
		frappe.throw(_("The second organization must be another organization."))
	if doc.is_new() and not doc.contacts_from and doc.pipeline:
		doc.contacts_from = frappe.db.get_value("CRM Pipeline", doc.pipeline, "default_contacts_from") or FIRST


def chosen_organizations(doc) -> list[tuple[str, str]]:
	"""[(role, organization)] whose contacts the card shows."""
	if not doc.second_organization:
		return [("organization", doc.organization)] if doc.organization else []
	choice = doc.contacts_from or FIRST
	first = [("organization", doc.organization)] if doc.organization else []
	second = [("second_organization", doc.second_organization)]
	return {FIRST: first, SECOND: second}.get(choice, first + second)


@frappe.whitelist()
def get_card_contacts(deal: str) -> dict:
	"""Contacts of the card's organizations, as `contacts_from` chooses: for each organization, its people and
	the phone and e-mail of its Receita record."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.check_permission("read")
	label = second_organization_label(doc.pipeline)
	return {
		"contacts_from": doc.contacts_from or FIRST,
		"second_organization_label": label,
		"organizations": [
			_organization(role, name, _("Organization") if role == "organization" else label)
			for role, name in chosen_organizations(doc)
		],
	}


def _organization(role: str, name: str, label: str) -> dict:
	meta = frappe.get_meta("CRM Organization")
	extra = [f for f in ("registry_phone", "registry_email") if meta.has_field(f)]
	values = frappe.db.get_value("CRM Organization", name, extra, as_dict=True) if extra else {}
	return {
		"role": role,
		"label": label,
		"name": name,
		"registry_phone": (values or {}).get("registry_phone"),
		"registry_email": (values or {}).get("registry_email"),
		"contacts": organization_contacts(name),
	}


def organization_contacts(organization: str) -> list[dict]:
	"""People linked to the organization (contact links or the contact's company), that the user can read."""
	linked = frappe.get_all(
		"Dynamic Link",
		filters={"parenttype": "Contact", "link_doctype": "CRM Organization", "link_name": organization},
		pluck="parent",
	)
	or_filters = {"company_name": organization}
	if linked:
		or_filters["name"] = ("in", linked)
	return frappe.get_list(
		"Contact",
		or_filters=or_filters,
		fields=["name", "full_name", "email_id", "mobile_no", "phone"],
		order_by="full_name asc",
		limit=CONTACTS_LIMIT,
	)
