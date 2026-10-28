import frappe

from crm.fcrm.doctype.crm_deal.crm_deal import default_card_name


def execute():
	"""Cards get a name (credtech#182): the organization, else the person. Saved views that used the
	organization as the kanban title use the card's name."""
	for name in frappe.db.sql_list("select name from `tabCRM Deal` where ifnull(deal_name, '') = ''"):
		doc = frappe.get_doc("CRM Deal", name)
		frappe.db.set_value("CRM Deal", name, "deal_name", default_card_name(doc), update_modified=False)
	frappe.db.sql(
		"""update `tabCRM View Settings` set title_field = 'deal_name'
		where dt = 'CRM Deal' and title_field = 'organization'"""
	)
