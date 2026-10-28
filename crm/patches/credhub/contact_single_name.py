import frappe


def execute():
	"""Contacts keep one name field, the full name (owner decision of 28/10/2026): the middle and last names join
	the first name. full_name already holds the joined name, so nothing changes on screen."""
	frappe.db.sql(
		"""update `tabContact`
		set first_name = trim(concat_ws(' ', nullif(trim(first_name), ''), nullif(trim(middle_name), ''),
				nullif(trim(last_name), ''))),
			middle_name = null, last_name = null
		where ifnull(middle_name, '') != '' or ifnull(last_name, '') != ''"""
	)
