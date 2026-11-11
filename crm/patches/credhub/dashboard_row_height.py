import json

import frappe


def execute():
	"""The dashboard grid row grew from 42px to 47.2px (Figma "Início · Visão geral" 819:2): scale saved
	layouts so charts keep their height, and metric cards drop from 3 rows to 2 (94px)."""
	for name in frappe.get_all("CRM Dashboard", pluck="name"):
		raw = frappe.db.get_value("CRM Dashboard", name, "layout")
		try:
			items = json.loads(raw or "[]")
		except ValueError:
			continue
		for item in items:
			layout = item.get("layout") or {}
			if item.get("type") == "number_chart" and layout.get("h") == 3:
				layout["h"] = 2
			elif layout.get("h"):
				layout["h"] = max(1, round(layout["h"] * 42 / 47.2))
			if layout.get("y"):
				layout["y"] = round(layout["y"] * 42 / 47.2)
		frappe.db.set_value("CRM Dashboard", name, "layout", json.dumps(items), update_modified=False)
