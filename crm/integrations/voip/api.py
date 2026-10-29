"""Screen-facing methods shared by every telephony operator (credtech#268): the extension of each
user and the click-to-call from a deal."""

import frappe
from frappe import _

from crm.integrations.voip.operators import OPERATORS, get_operator, get_operator_by_medium


def get_known_operator(key: str):
	if key not in OPERATORS:
		frappe.throw(_("Unknown telephony operator: {0}").format(key))
	return get_operator(key)


@frappe.whitelist()
def get_extensions(operator: str) -> dict:
	"""{user: extension} at this operator, for its settings screen."""
	operator = get_known_operator(operator)
	frappe.has_permission(operator.settings_doctype, "write", throw=True)
	rows = frappe.get_all(
		"CRM Telephony Extension",
		filters={"parenttype": "CRM Telephony Agent", "medium": operator.medium},
		fields=["parent", "extension"],
	)
	return {row.parent: row.extension for row in rows}


@frappe.whitelist()
def set_extension(operator: str, user: str, extension: str | None = None) -> dict:
	"""Extension of a user at the operator; empty removes it. It is how a call reaches the timeline
	of the right salesperson, and the line a click-to-call rings first."""
	operator = get_known_operator(operator)
	frappe.has_permission(operator.settings_doctype, "write", throw=True)
	extension = (extension or "").strip() or None

	if frappe.db.exists("CRM Telephony Agent", user):
		agent = frappe.get_doc("CRM Telephony Agent", user)
	else:
		agent = frappe.new_doc("CRM Telephony Agent")
		agent.user = user
	agent.set_extension(operator.medium, extension)
	agent.save(ignore_permissions=True)
	return {"user": user, "extension": extension}


def callable_operators() -> list:
	"""Enabled operators the CRM can place a call through."""
	return [operator for operator in OPERATORS.values() if operator.can_originate and operator.is_enabled()]


@frappe.whitelist()
def make_call(number: str, medium: str | None = None, deal: str | None = None) -> dict:
	"""Click-to-call: the operator rings the salesperson's extension, then `number`. The deal goes
	with the call so it lands on that deal's timeline (else on the open deals of the number)."""
	if not number:
		frappe.throw(_("No phone number to call."))
	operator = get_operator_by_medium(medium) if medium else None
	if not operator:
		default = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")
		operator = get_operator_by_medium(default)
	operators = callable_operators()
	if operator not in operators:
		if len(operators) != 1:
			frappe.throw(_("Choose the telephony to call with in the telephony settings."))
		operator = operators[0]

	extension = None
	if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		extension = frappe.get_doc("CRM Telephony Agent", frappe.session.user).get_extension(operator.medium)
	if not extension:
		frappe.throw(
			_("You have no {0} extension. Ask a manager to set it in the telephony settings.").format(
				operator.medium
			)
		)

	# only a deal this user can see goes with the call
	if deal and not (frappe.db.exists("CRM Deal", deal) and frappe.has_permission("CRM Deal", "read", deal)):
		deal = None

	call_id = operator.originate_call(operator.get_settings(), extension, number, deal)
	return {"medium": operator.medium, "id": call_id}
