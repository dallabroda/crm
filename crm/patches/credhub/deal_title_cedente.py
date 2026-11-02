import frappe


def execute():
	"""Cedente on each title (credtech#315): titles imported before the field get the cedente of their card
	(second organization), so the card can later be grouped by debtor only without losing who sold each title."""
	if not frappe.db.has_column("CRM Deal Title", "cedente"):
		return
	frappe.db.sql(
		"""update `tabCRM Deal Title` t join `tabCRM Deal` d on d.name = t.parent
		set t.cedente = d.second_organization
		where t.parenttype = 'CRM Deal' and ifnull(t.cedente, '') = '' and ifnull(d.second_organization, '') != ''"""
	)
