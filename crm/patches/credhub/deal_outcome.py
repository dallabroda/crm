import frappe


def execute():
	"""Card status (credtech#315): cards sitting in a stage of type Won or Lost start Won or Lost; the rest keep the
	default "In progress"."""
	if not frappe.db.has_column("CRM Deal", "outcome"):
		return
	frappe.db.sql(
		"""update `tabCRM Deal` d join `tabCRM Deal Status` s on s.name = d.status
		set d.outcome = s.type
		where s.type in ('Won', 'Lost')"""
	)
	frappe.db.sql("update `tabCRM Deal` set outcome = 'In progress' where ifnull(outcome, '') = ''")
