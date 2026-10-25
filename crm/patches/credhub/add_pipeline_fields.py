import frappe

from crm.fcrm.doctype.crm_pipeline.fields import setup_default_fields


def execute():
	"""Existing pipelines start with the standard fields, all visible, optional and editable."""
	for pipeline in frappe.get_all("CRM Pipeline", pluck="name"):
		setup_default_fields(pipeline)
