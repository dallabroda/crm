"""Sandbox records of the HubTech API (credtech#375): no automation, ERP or notification side effects.

The HubTech app (cred_hub) gives test API keys a Sandbox pipeline (CRM Pipeline flagged `credhub_sandbox`) and stamps
the records created by a test key with the same column (Contact, CRM Organization, CRM Lead, FCRM Note, CRM Task,
File). The client decides what costs money or reaches people, so nothing automatic runs for that test data:

- automation flows: CRM events are not emitted, and any flow queued against a sandbox record (doc events, date or
  cron triggers, custom events, resumed waits) is parked as Skipped before it runs;
- Notification and Webhook documents of Frappe do not fire for sandbox records;
- assignment rules and the pipeline distribution do not hand sandbox records to salespeople, and the CRM does not
  notify anyone about them;
- the ERPNext customer sync and the website enrichment do not run for them.

The crm only reads the flags, and only where the column exists: without cred_hub nothing is ever sandbox.
"""

import frappe

FLAG = "credhub_sandbox"
STAMPED = ("Contact", "CRM Organization", "CRM Lead", "FCRM Note", "CRM Task", "File")
# Records that belong to the record they point at: (field with the doctype, field with the name)
REFERENCES = {
	"FCRM Note": ("reference_doctype", "reference_docname"),
	"CRM Task": ("reference_doctype", "reference_docname"),
	"CRM Call Log": ("reference_doctype", "reference_docname"),
	"File": ("attached_to_doctype", "attached_to_name"),
	"Communication": ("reference_doctype", "reference_name"),
	"Comment": ("reference_doctype", "reference_name"),
	"WhatsApp Message": ("reference_doctype", "reference_name"),
	"ToDo": ("reference_type", "reference_name"),
	"CRM Notification": ("reference_doctype", "reference_name"),
}
# Doctypes that carry a pipeline: in a flagged pipeline they are sandbox
PIPELINE_DOCTYPES = ("CRM Deal", "CRM Lead")
# Doctypes that get the SandboxDocument mixin (extend_doctype_class in hooks.py)
GUARDED_DOCTYPES = ("CRM Deal", *STAMPED)


def has_flag(doctype: str | None) -> bool:
	if not doctype:
		return False
	try:
		return frappe.get_meta(doctype).has_field(FLAG)
	except frappe.DoesNotExistError:
		return False


def is_sandbox_pipeline(pipeline: str | None) -> bool:
	return (
		bool(pipeline)
		and has_flag("CRM Pipeline")
		and bool(frappe.get_cached_value("CRM Pipeline", pipeline, FLAG))
	)


def is_sandbox(doc) -> bool:
	"""Whether `doc` (a Document or a dict with its doctype) is sandbox data: in a Sandbox pipeline, stamped by a
	test key, or pointing at a sandbox record."""
	if not doc:
		return False
	doctype = doc.get("doctype")
	if doctype in PIPELINE_DOCTYPES and is_sandbox_pipeline(doc.get("pipeline")):
		return True
	if doctype in STAMPED and doc.get(FLAG):
		return True
	reference = REFERENCES.get(doctype)
	if reference:
		return is_sandbox_record(doc.get(reference[0]), doc.get(reference[1]))
	return False


def is_sandbox_record(doctype: str | None, name: str | None) -> bool:
	"""Same as is_sandbox, read from the database. Memoized for the request: the flag never changes."""
	if not doctype or not name or not isinstance(name, str):
		return False
	fields = []
	if doctype in PIPELINE_DOCTYPES:
		fields.append("pipeline")
	if doctype in STAMPED and has_flag(doctype):
		fields.append(FLAG)
	if doctype in REFERENCES:
		fields.extend(REFERENCES[doctype])
	if not fields:
		return False
	memo = getattr(frappe.local, "crm_sandbox_records", None)
	if memo is None:
		memo = frappe.local.crm_sandbox_records = {}
	key = (doctype, name)
	if key not in memo:
		try:
			values = frappe.db.get_value(doctype, name, fields, as_dict=True)
		except frappe.DoesNotExistError:
			values = None
		# a record not written yet is not memoized: it may be the one being created
		if not values:
			return False
		memo[key] = is_sandbox(frappe._dict(values, doctype=doctype))
	return memo[key]


# ---------- Entry points ----------


def skip_sandbox_trigger(doc, method=None):
	"""Automation Trigger Queue.before_insert: a flow queued against a sandbox record never runs (Skipped rows are
	not claimed by the drainer)."""
	if doc.get("status") in ("Pending", "Scheduled") and is_sandbox_record(
		doc.get("ref_doctype"), doc.get("ref_name")
	):
		doc.status = "Skipped"


class SandboxDocument:
	"""Mixin of GUARDED_DOCTYPES: Frappe's Notification and Webhook documents do not fire for sandbox records."""

	def run_notifications(self, method):
		if is_sandbox(self):
			return
		return super().run_notifications(method)

	def run_method(self, method, *args, **kwargs):
		out = super().run_method(method, *args, **kwargs)
		# run_webhooks has no hook: drop what it queued for this record (sent only after the commit)
		queue = getattr(frappe.local, "_webhook_queue", None)
		if queue and any(execution.doc is self for execution in queue) and is_sandbox(self):
			queue[:] = [execution for execution in queue if execution.doc is not self]
		return out
