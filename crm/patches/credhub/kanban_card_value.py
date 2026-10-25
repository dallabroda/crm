import json

import frappe

OLD = ["annual_revenue", "email", "mobile_no", "_assign", "modified"]
# first version of this patch, which still showed the assignees (almost always the owner again)
WITH_ASSIGN = ["deal_value", "deal_owner", "_assign", "modified"]
NEW = ["deal_value", "deal_owner", "modified"]


def execute():
	"""Saved card Kanban views still on an old default (the organization's annual revenue, usually
	empty, or the owner shown twice) switch to the card's own value and owner."""
	views = frappe.get_all(
		"CRM View Settings", {"dt": "CRM Deal", "type": "kanban"}, ["name", "kanban_fields"]
	)
	for view in views:
		try:
			fields = json.loads(view.kanban_fields or "[]")
		except ValueError:
			continue
		if fields in (OLD, WITH_ASSIGN):
			frappe.db.set_value("CRM View Settings", view.name, "kanban_fields", json.dumps(NEW))
