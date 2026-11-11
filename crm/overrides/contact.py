# import frappe
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	@staticmethod
	def default_list_data():
		# Figma column widths at 1440px (the list grid sizes to its content, so
		# proportions would grow with long names); last modified right aligned
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "full_name",
				"width": "21.0625rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "14.875rem",
			},
			{
				"label": "Phone",
				"type": "Data",
				"key": "mobile_no",
				"width": "14.875rem",
			},
			{
				"label": "Organization",
				"type": "Data",
				"key": "company_name",
				"width": "14.875rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "9.9375rem",
				"align": "right",
			},
		]
		rows = [
			"name",
			"full_name",
			"company_name",
			"email_id",
			"mobile_no",
			"modified",
			"image",
		]
		return {"columns": columns, "rows": rows}
