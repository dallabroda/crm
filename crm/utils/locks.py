# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Site-wide lock for flows that create contacts and organizations.

Two such flows running at the same time (e.g. several leads converted at once, or automatic
entries arriving together) deadlock in the database on the organization's primary key: both take
a gap lock and then both try to insert into that gap. They are short, so they run one at a time.
"""

import frappe
from frappe import _

LOCK_TIMEOUT = 30  # seconds


def acquire_record_creation_lock():
	"""Hold the lock until this transaction commits or rolls back (no-op if already held)."""
	if frappe.flags.get("crm_record_creation_lock") or frappe.db.db_type != "mariadb":
		return
	name = _lock_name()
	if not frappe.db.sql("select get_lock(%s, %s)", (name, LOCK_TIMEOUT))[0][0]:
		frappe.throw(_("The system is busy creating other records. Try again in a moment."))
	frappe.flags.crm_record_creation_lock = True

	def release():
		if frappe.flags.get("crm_record_creation_lock"):
			frappe.flags.crm_record_creation_lock = False
			frappe.db.sql("select release_lock(%s)", (name,))

	frappe.db.after_commit.add(release)
	frappe.db.after_rollback.add(release)


def _lock_name() -> str:
	# Lock names are server-wide in MariaDB; the database name keeps sites apart (max 64 chars)
	return f"crm_records:{frappe.conf.db_name}"[:64]
