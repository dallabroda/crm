import frappe
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter

from crm.patches.credhub.field_removal import strip_field


def execute():
	"""Owner decision (credtech#80): a card has one value, "Deal Value" (filled from the products
	total when it has products). "Expected Deal Value" leaves the screens; values typed only
	there move to the card value, so nothing is lost."""
	frappe.db.sql(
		"""update `tabCRM Deal` set deal_value = expected_deal_value
		where ifnull(deal_value, 0) = 0 and ifnull(expected_deal_value, 0) != 0"""
	)
	strip_field("expected_deal_value")
	frappe.db.set_single_value("FCRM Settings", "auto_update_expected_deal_value", 0)
	# forecasting made the old field mandatory; the card value takes its place
	if frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
		delete_property_setter("CRM Deal", "reqd", "expected_deal_value")
		make_property_setter("CRM Deal", "deal_value", "reqd", 1, "Check")
