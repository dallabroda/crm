import frappe

from crm.fcrm.doctype.crm_pipeline.fields import MOVED_TO_ORGANIZATION, is_empty
from crm.patches.credhub.field_removal import strip_layouts, strip_pipelines


def execute():
	"""Owner decision 7 of 28/10/2026 (credtech#181): site, annual revenue, number of employees and industry
	belong to the organization. The card's values go to its organization where the organization has none
	(a filled organization field is never replaced; among cards of the same organization, the most recently
	changed card with a value wins). Then the fields leave the card form: pipelines and card layouts. The
	card columns and their values stay."""
	copy_to_organizations()
	for field in MOVED_TO_ORGANIZATION:
		strip_layouts(field)
		strip_pipelines(field)


def copy_to_organizations():
	deal_meta = frappe.get_meta("CRM Deal")
	org_meta = frappe.get_meta("CRM Organization")
	fields = [f for f in MOVED_TO_ORGANIZATION if deal_meta.has_field(f) and org_meta.has_field(f)]
	if not fields:
		return
	cards = frappe.get_all(
		"CRM Deal",
		filters={"organization": ("is", "set")},
		fields=["organization", *fields],
		order_by="modified desc",
	)
	values = {}
	for card in cards:
		for field in fields:
			if not is_empty(deal_meta.get_field(field), card[field]):
				values.setdefault(card.organization, {}).setdefault(field, card[field])
	for organization, found in values.items():
		current = frappe.db.get_value("CRM Organization", organization, list(found), as_dict=True)
		if not current:
			continue
		update = {f: v for f, v in found.items() if is_empty(org_meta.get_field(f), current[f])}
		if update:
			frappe.db.set_value("CRM Organization", organization, update, update_modified=False)
