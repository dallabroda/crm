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
# A call that fails to record holds the cursor so it is read again on the next runs, for up to a day
MAX_RETRY = timedelta(days=1)


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

	cursor = started
	for call in calls:
		try:
			# commits each call on its own: a later failure doesn't undo it
			record_call(call, operator.medium)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"{operator.medium}: error while recording a call")
			cursor = min(cursor, retry_from(call, since))

	frappe.db.set_default(cursor_key, str(max(cursor, started - MAX_RETRY)))
	frappe.db.commit()


def retry_from(call: dict, since):
	"""Where the next run must start reading for this failed call to come again: its start time,
	or the window just read when it has none."""
	try:
		# get_datetime(None) is "now", which would let the call go
		return get_datetime(call["start_time"]) if call.get("start_time") else since
	except Exception:
		return since
