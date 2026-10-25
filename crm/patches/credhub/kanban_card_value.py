import json

import frappe

OLD = ["annual_revenue", "email", "mobile_no", "_assign", "modified"]
NEW = ["deal_value", "deal_owner", "_assign", "modified"]


def execute():
	"""Saved card Kanban views still on the old default showed the organization's annual revenue
	(usually empty) as the card value; switch them to the card's own value and owner."""
	views = frappe.get_all(
		"CRM View Settings", {"dt": "CRM Deal", "type": "kanban"}, ["name", "kanban_fields"]
	)
	for view in views:
		try:
			fields = json.loads(view.kanban_fields or "[]")
		except ValueError:
			continue
		if fields == OLD:
			frappe.db.set_value("CRM View Settings", view.name, "kanban_fields", json.dumps(NEW))
