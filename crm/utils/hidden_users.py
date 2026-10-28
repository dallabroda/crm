# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Users other apps hide from the CRM: technical users (e.g. the user behind an API key).

An app lists them with the `crm_hidden_users` hook (dotted paths of functions returning user names).
They keep working (permissions, pipeline membership), but do not show up as CRM users, are not listed
as pipeline members and never receive cards from the distribution.
"""

import frappe


def hidden_users() -> set[str]:
	users = set()
	for method in frappe.get_hooks("crm_hidden_users"):
		users.update(frappe.get_attr(method)() or [])
	return users
