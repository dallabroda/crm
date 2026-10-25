import json

import frappe

FIELD = "probability"


def execute():
	"""Owner decision (credtech#81): Probability leaves the Cred Hub. The column stays (no data is
	dropped); it only leaves layouts, filters, saved views, pipelines and the dashboard."""
	strip_layouts()
	strip_quick_filters()
	strip_views()
	strip_pipelines()
	drop_forecast_chart()
	frappe.db.delete("CRM Form Script", {"name": "Forecasting Script"})


def _without_field(node):
	"""Remove the field from any nested layout structure (lists of names or of field dicts)."""
	if isinstance(node, list):
		return [_without_field(item) for item in node if not _is_field(item)]
	if isinstance(node, dict):
		return {key: _without_field(value) for key, value in node.items()}
	return node


def _is_field(item):
	if item == FIELD:
		return True
	return isinstance(item, dict) and (item.get("fieldname") == FIELD or item.get("key") == FIELD)


def _load(value, default):
	try:
		return json.loads(value) if value else default
	except ValueError:
		return None


def strip_layouts():
	for name, layout in frappe.get_all(
		"CRM Fields Layout", {"dt": "CRM Deal"}, ["name", "layout"], as_list=True
	):
		data = _load(layout, [])
		if data is None:
			continue
		cleaned = _without_field(data)
		if cleaned != data:
			frappe.db.set_value("CRM Fields Layout", name, "layout", json.dumps(cleaned))


def strip_quick_filters():
	for name, value in frappe.get_all(
		"CRM Global Settings", {"dt": "CRM Deal"}, ["name", "json"], as_list=True
	):
		data = _load(value, [])
		if isinstance(data, list) and FIELD in data:
			frappe.db.set_value(
				"CRM Global Settings", name, "json", json.dumps([f for f in data if f != FIELD])
			)


def strip_views():
	views = frappe.get_all(
		"CRM View Settings", {"dt": "CRM Deal"}, ["name", "columns", "rows", "kanban_fields", "filters"]
	)
	for view in views:
		changes = {}
		for key in ("columns", "rows", "kanban_fields"):
			data = _load(view[key], [])
			if isinstance(data, list):
				cleaned = _without_field(data)
				if cleaned != data:
					changes[key] = json.dumps(cleaned)
		filters = _load(view.filters, {})
		if isinstance(filters, dict) and FIELD in filters:
			filters.pop(FIELD)
			changes["filters"] = json.dumps(filters)
		if changes:
			frappe.db.set_value("CRM View Settings", view.name, changes)


def strip_pipelines():
	frappe.db.delete("CRM Pipeline Field", {"parenttype": "CRM Pipeline", "fieldname": FIELD})
	frappe.db.delete("CRM Pipeline Field Rule", {"parenttype": "CRM Pipeline", "fieldname": FIELD})


def drop_forecast_chart():
	for name, layout in frappe.get_all("CRM Dashboard", fields=["name", "layout"], as_list=True):
		data = _load(layout, [])
		if not isinstance(data, list):
			continue
		cleaned = [item for item in data if item.get("name") != "forecasted_revenue"]
		if len(cleaned) != len(data):
			frappe.db.set_value("CRM Dashboard", name, "layout", json.dumps(cleaned))
