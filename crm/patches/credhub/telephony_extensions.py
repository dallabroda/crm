import frappe


def execute():
	"""API4Com extensions move from CRM Telephony Agent.api4com_extension to the per-operator
	extensions table (credtech#268). Frappe keeps the old column after the field is removed."""
	if not frappe.db.has_column("CRM Telephony Agent", "api4com_extension"):
		return
	rows = frappe.db.sql(
		"""select name, api4com_extension from `tabCRM Telephony Agent`
		where ifnull(api4com_extension, '') != ''""",
		as_dict=True,
	)
	for row in rows:
		extension = row.api4com_extension.strip()
		if not extension:
			continue
		if frappe.db.exists(
			"CRM Telephony Extension",
			{"parenttype": "CRM Telephony Agent", "parent": row.name, "medium": "API4Com"},
		):
			continue
		# straight insert: a migration must not stop on a validation of the agent
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Extension",
				"parent": row.name,
				"parenttype": "CRM Telephony Agent",
				"parentfield": "extensions",
				"idx": 1,
				"medium": "API4Com",
				"extension": extension,
			}
		).db_insert()
