import frappe


def execute():
	"""Funnel fields and rules saved before the blocks (credtech#196) are the card's own fields."""
	for table in ("CRM Pipeline Field", "CRM Pipeline Field Rule"):
		frappe.db.sql(f"update `tab{table}` set block = 'Card' where ifnull(block, '') = ''")
