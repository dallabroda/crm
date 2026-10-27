# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Dynamic forms API (credtech#178): the form of cards, contacts and companies in a context.

Routes /api/method/crm.api.forms.* (prefix agreed with the API keys proposal). Phase 1 has the schema;
creating fields and saving the configuration come in the next phases.
"""

import frappe
from frappe import _

from crm.fcrm.doctype.crm_pipeline import form_schema


@frappe.whitelist()
def get_form_schema(doctype: str, pipeline: str | None = None, stage: str | None = None) -> dict:
	"""Fields of the form in order, each with visible, required, read only and locked for the context."""
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if doctype == "CRM Deal" and pipeline:
		from crm.api.pipeline import _assert_can_view

		_assert_can_view(pipeline)
	return form_schema.get_form_schema(doctype, pipeline, stage)
