# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Email accounts of the platform (credtech#191).

The account that sends the platform's own emails (invites, password resets, notices, leads) belongs to the
platform, not to the company: apps name it with the `crm_system_email_accounts` hook (cred_hub: "HubTech
CRM", formerly "Cred Hub"). It is left out of Settings > Email > Accounts and only Administrator, which is
who runs the setup scripts, can change, rename or delete it.
"""

import frappe
from frappe import _


def system_email_accounts() -> list[str]:
	return list(frappe.get_hooks("crm_system_email_accounts") or [])


@frappe.whitelist()
def get_system_email_accounts() -> list[str]:
	"""Names of the platform's accounts, so the accounts screen leaves them out."""
	return system_email_accounts()


def _assert_can_change(name: str | None):
	if name and name in system_email_accounts() and frappe.session.user != "Administrator":
		frappe.throw(
			_("This account sends the system emails and is managed by CredTech."),
			frappe.PermissionError,
			title=_("System email account"),
		)


def before_validate(doc, method=None):
	# before Frappe's own validate, which tests the mail servers
	_assert_can_change(doc.name or doc.email_account_name)


def on_trash(doc, method=None):
	_assert_can_change(doc.name)


def before_rename(doc, method=None, old=None, new=None, merge=False):
	_assert_can_change(old)
	_assert_can_change(new)
