import json

import frappe


def strip_field(field):
	"""Take a CRM Deal field out of saved layouts, quick filters, views and pipelines.
	The column and its data stay; only the screens stop offering it."""
	strip_layouts(field)
	strip_quick_filters(field)
	strip_views(field)
	strip_pipelines(field)


def _without_field(node, field):
	"""Remove the field from any nested layout structure (lists of names or of field dicts)."""
	if isinstance(node, list):
		return [_without_field(item, field) for item in node if not _is_field(item, field)]
	if isinstance(node, dict):
		return {key: _without_field(value, field) for key, value in node.items()}
	return node


def _is_field(item, field):
	if item == field:
		return True
	return isinstance(item, dict) and (item.get("fieldname") == field or item.get("key") == field)


def _load(value, default):
	try:
		return json.loads(value) if value else default
	except ValueError:
		return None


def strip_layouts(field):
	for name, layout in frappe.get_all(
		"CRM Fields Layout", {"dt": "CRM Deal"}, ["name", "layout"], as_list=True
	):
		data = _load(layout, [])
		if data is None:
			continue
		cleaned = _without_field(data, field)
		if cleaned != data:
			frappe.db.set_value("CRM Fields Layout", name, "layout", json.dumps(cleaned))


def strip_quick_filters(field):
	for name, value in frappe.get_all(
		"CRM Global Settings", {"dt": "CRM Deal"}, ["name", "json"], as_list=True
	):
		data = _load(value, [])
		if isinstance(data, list) and field in data:
			frappe.db.set_value(
				"CRM Global Settings", name, "json", json.dumps([f for f in data if f != field])
			)


def strip_views(field):
	views = frappe.get_all(
		"CRM View Settings", {"dt": "CRM Deal"}, ["name", "columns", "rows", "kanban_fields", "filters"]
	)
	for view in views:
		changes = {}
		for key in ("columns", "rows", "kanban_fields"):
			data = _load(view[key], [])
			if isinstance(data, list):
				cleaned = _without_field(data, field)
				if cleaned != data:
					changes[key] = json.dumps(cleaned)
		filters = _load(view.filters, {})
		if isinstance(filters, dict) and field in filters:
			filters.pop(field)
			changes["filters"] = json.dumps(filters)
		if changes:
			frappe.db.set_value("CRM View Settings", view.name, changes)


def strip_pipelines(field):
	frappe.db.delete("CRM Pipeline Field", {"parenttype": "CRM Pipeline", "fieldname": field})
	frappe.db.delete("CRM Pipeline Field Rule", {"parenttype": "CRM Pipeline", "fieldname": field})
