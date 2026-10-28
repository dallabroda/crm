# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.rate_limiter import rate_limit

from crm.api.user import validate_no_role_profile

# Days a pending invitation stays valid (expire_invitations); also said in the e-mail
INVITATION_DAYS = 3


class CRMInvitation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		accepted_at: DF.Datetime | None
		email: DF.Data
		email_sent_at: DF.Datetime | None
		invited_by: DF.Link | None
		key: DF.Data | None
		role: DF.Literal["", "Sales User", "Sales Manager", "System Manager"]
		status: DF.Literal["", "Pending", "Accepted", "Expired"]
	# end: auto-generated types

	def before_insert(self):
		frappe.utils.validate_email_address(self.email, True)
		self.validate_existing_user()

		self.key = frappe.generate_hash(length=12)
		self.invited_by = frappe.session.user
		self.status = "Pending"

	def after_insert(self):
		self.invite_via_email()

	def invite_via_email(self):
		invite_link = frappe.utils.get_url(f"/api/method/crm.api.accept_invitation?key={self.key}")
		if frappe.local.dev_server:
			print(f"Invite link for {self.email}: {invite_link}")  # nosemgrep

		title = "HubTech CRM"
		template = "crm_invitation"
		# Who invited and to which company (Settings > Brand), so the e-mail says it
		company = frappe.db.get_single_value("FCRM Settings", "brand_name") or None
		# "Administrator" is the setup account, not a person: the e-mail then says who invites in general terms
		person = self.invited_by not in (None, "", "Administrator", "Guest")
		inviter = frappe.utils.get_fullname(self.invited_by) if person else None
		if inviter and company:
			subject = _("{0} invited you to {1} on HubTech CRM").format(inviter, company)
		else:
			subject = _("You have been invited to join {0}").format(company or title)

		frappe.sendmail(
			recipients=self.email,
			subject=subject,
			template=template,
			args={
				"title": title,
				"invite_link": invite_link,
				"inviter": inviter,
				"company": company,
				"role": self.role,
				"email": self.email,
				"days": INVITATION_DAYS,
			},
			now=True,
		)
		self.db_set("email_sent_at", frappe.utils.now())

	@frappe.whitelist()
	def accept_invitation(self):
		frappe.only_for(["System Manager", "Sales Manager"], True)
		if self.accept():
			# the invitee was not around to set a password, mail them a link to do it
			frappe.get_doc("User", self.email).send_welcome_mail_to_user()

	def valid_until(self):
		"""The invitation is valid for INVITATION_DAYS from the last e-mail (a resend renews it)."""
		return valid_until(self.email_sent_at, self.creation)

	def accept(self):
		if self.status == "Pending" and frappe.utils.now_datetime() > self.valid_until():
			# the daily job may not have run yet: an old link must not get in
			self.db_set("status", "Expired")
		if self.status != "Pending":
			frappe.throw(_("Invalid or expired key"))

		user, is_new_user = self.create_user_if_not_exists()
		if not is_new_user:
			validate_no_role_profile(user)
		user.append_roles(self.role)
		if self.role == "System Manager":
			user.append_roles("Sales Manager", "Sales User")
		elif self.role == "Sales Manager":
			user.append_roles("Sales User")
		if self.role == "Sales User":
			self.update_module_in_user(user, "FCRM")
		user.save(ignore_permissions=True)

		self.status = "Accepted"
		self.accepted_at = frappe.utils.now()
		self.key = None
		self.save(ignore_permissions=True)

		return is_new_user

	def update_module_in_user(self, user, module):
		block_modules = frappe.get_all(
			"Module Def",
			fields=["name as module"],
			filters={"name": ["!=", module]},
		)

		if block_modules:
			user.set("block_modules", block_modules)

	def validate_existing_user(self):
		# the invite would be accepted but the role never applied, so fail early
		if frappe.db.exists("User", self.email):
			validate_no_role_profile(frappe.get_doc("User", self.email))

	def create_user_if_not_exists(self):
		if not frappe.db.exists("User", self.email):
			first_name = self.email.split("@")[0].title()
			user = frappe.get_doc(
				doctype="User",
				user_type="System User",
				email=self.email,
				send_welcome_email=0,
				first_name=first_name,
				default_app="crm",
			).insert(ignore_permissions=True)
			return user, True

		return frappe.get_doc("User", self.email), False


def valid_until(email_sent_at, creation):
	return frappe.utils.add_days(frappe.utils.get_datetime(email_sent_at or creation), INVITATION_DAYS)


def expire_invitations():
	"""expire invitations INVITATION_DAYS days after the last e-mail"""
	now = frappe.utils.now_datetime()
	pending = frappe.db.get_all(
		"CRM Invitation", filters={"status": "Pending"}, fields=["name", "email_sent_at", "creation"]
	)
	for row in pending:
		if valid_until(row.email_sent_at, row.creation) < now:
			invitation = frappe.get_doc("CRM Invitation", row.name)
			invitation.status = "Expired"
			invitation.save(ignore_permissions=True)


def _assert_can_invite(role: str):
	"""Same rule as crm.api.invite_by_email: managers invite salespeople, admins invite anyone."""
	frappe.only_for(["Sales Manager", "System Manager"], True)
	if role in ("System Manager", "Sales Manager") and "System Manager" not in frappe.get_roles():
		frappe.throw(_("You are not allowed to invite {0}").format(_(role)), frappe.PermissionError)


@frappe.whitelist()
def get_invitations() -> list[dict]:
	"""Invitations not accepted yet (pending or expired), newest first, with who invited, when the last
	e-mail went out and until when the link works."""
	frappe.only_for(["Sales Manager", "System Manager"], True)
	now = frappe.utils.now_datetime()
	rows = frappe.db.get_all(
		"CRM Invitation",
		filters={"status": ("in", ("Pending", "Expired"))},
		fields=["name", "email", "role", "status", "invited_by", "email_sent_at", "creation"],
		order_by="creation desc",
	)
	for row in rows:
		row.sent_on = row.email_sent_at or row.creation
		row.valid_until = valid_until(row.email_sent_at, row.creation)
		row.expired = row.status == "Expired" or row.valid_until < now
		row.invited_by_name = frappe.utils.get_fullname(row.invited_by) if row.invited_by else None
	return rows


@frappe.whitelist(methods=["POST"])
# the same invitation, from the same place: at most 3 e-mails an hour
@rate_limit(key="name", limit=3, seconds=60 * 60)
def resend_invitation(name: str) -> str:
	"""Send the invitation e-mail again, valid for INVITATION_DAYS more. An expired one becomes a new
	invitation (so the plan's seat check runs again) and the old record goes away."""
	invitation = frappe.get_doc("CRM Invitation", name)
	_assert_can_invite(invitation.role)
	if invitation.status not in ("Pending", "Expired"):
		frappe.throw(_("This invitation was already accepted."))
	if invitation.status == "Expired" or frappe.utils.now_datetime() > invitation.valid_until():
		renewed = frappe.get_doc(
			{"doctype": "CRM Invitation", "email": invitation.email, "role": invitation.role}
		).insert(ignore_permissions=True)
		frappe.delete_doc("CRM Invitation", invitation.name, ignore_permissions=True)
		return renewed.name
	invitation.invite_via_email()
	return invitation.name
