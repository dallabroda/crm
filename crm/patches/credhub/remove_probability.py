import json

import frappe

from crm.patches.credhub.field_removal import strip_field


def execute():
	"""Owner decision (credtech#81): Probability leaves the Cred Hub. The column stays (no data is
	dropped); it only leaves layouts, filters, saved views, pipelines and the dashboard."""
	strip_field("probability")
	drop_forecast_chart()
	frappe.db.delete("CRM Form Script", {"name": "Forecasting Script"})


def _load(value, default):
	try:
		return json.loads(value) if value else default
	except ValueError:
		return None


def drop_forecast_chart():
	for name, layout in frappe.get_all("CRM Dashboard", fields=["name", "layout"], as_list=True):
		data = _load(layout, [])
		if not isinstance(data, list):
			continue
		cleaned = [item for item in data if item.get("name") != "forecasted_revenue"]
		if len(cleaned) != len(data):
			frappe.db.set_value("CRM Dashboard", name, "layout", json.dumps(cleaned))
