"""Polling of operators that have no call webhook (credtech#268): every 5 minutes their recent calls
are read from the API and recorded like a webhook would, one call log per call id."""

from datetime import timedelta

import frappe
from frappe.utils import get_datetime, now_datetime

from crm.integrations.voip.operators import OPERATORS
from crm.integrations.voip.webhook import record_call

# Calls still ringing or whose recording isn't ready get read again on the next runs
OVERLAP = timedelta(minutes=30)
# A newly enabled operator brings the last hour, not its whole history
FIRST_LOOKBACK = timedelta(hours=1)


def poll_calls():
	for operator in OPERATORS.values():
		if operator.polls and operator.is_enabled():
			poll(operator)


def poll(operator):
	cursor_key = f"crm_voip_poll_cursor_{operator.key}"
	last_run = frappe.db.get_default(cursor_key)
	started = now_datetime()
	since = get_datetime(last_run) - OVERLAP if last_run else started - FIRST_LOOKBACK

	try:
		calls = operator.list_calls(operator.get_settings(), since)
	except Exception:
		# cursor kept: the same window is read again on the next run
		frappe.log_error(title=f"{operator.medium}: could not read the calls")
		return

	for call in calls:
		try:
			record_call(call, operator.medium)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"{operator.medium}: error while recording a call")

	# a call that failed is read again while it is inside the overlap window
	frappe.db.set_default(cursor_key, str(started))
	frappe.db.commit()
