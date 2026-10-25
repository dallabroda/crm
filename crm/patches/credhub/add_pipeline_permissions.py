import frappe

from crm.install import add_pipeline_owner_role


def execute():
	"""Keep current access after pipelines start restricting cards: every CRM user becomes a member
	of the existing pipelines (admins see everything anyway)."""
	add_pipeline_owner_role()
	users = frappe.get_all(
		"Has Role",
		{"parenttype": "User", "role": ("in", ("Sales User", "Sales Manager"))},
		pluck="parent",
		distinct=True,
	)
	users = [
		u for u in users if u not in ("Administrator", "Guest") and frappe.db.get_value("User", u, "enabled")
	]
	for pipeline in frappe.get_all("CRM Pipeline", pluck="name"):
		doc = frappe.get_doc("CRM Pipeline", pipeline)
		current = {m.user for m in doc.members}
		for user in users:
			if user not in current:
				doc.append("members", {"user": user, "role": "Member"})
		doc.save(ignore_permissions=True)
