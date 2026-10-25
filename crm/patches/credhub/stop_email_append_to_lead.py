import frappe


def execute():
	"""E-mail accounts set up by the CRM appended unknown e-mails to CRM Lead, which now would create
	leads outside any pipeline (hidden). Cards from e-mails come only from "create from incoming
	e-mails" with its pipeline."""
	frappe.db.set_value("Email Account", {"append_to": "CRM Lead"}, "append_to", None, update_modified=False)
	frappe.db.set_value("IMAP Folder", {"append_to": "CRM Lead"}, "append_to", None, update_modified=False)
