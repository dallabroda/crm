import frappe


@frappe.whitelist()
def get_assignment_rules_list():
	assignment_rules = []
	for docname in frappe.get_all(
		"Assignment Rule", filters={"document_type": ["in", ["CRM Lead", "CRM Deal"]]}
	):
		doc = frappe.get_value(
			"Assignment Rule",
			docname,
			fieldname=[
				"name",
				"description",
				"disabled",
				"priority",
				# what the list shows in "Funil" and "Como distribui" (Figma 2335:10136)
				"rule",
				"field",
				"assign_condition_json",
			],
			as_dict=True,
		)
		users = frappe.get_all(
			"Assignment Rule User", {"parent": docname.name}, pluck="user", order_by="idx asc"
		)
		assignment_rules.append({**doc, "users_exists": bool(users), "users": users})
	return assignment_rules


@frappe.whitelist()
def duplicate_assignment_rule(docname: str, new_name: str):
	doc = frappe.get_doc("Assignment Rule", docname)
	doc.name = new_name
	doc.assignment_rule_name = new_name
	doc.insert()
	return doc
