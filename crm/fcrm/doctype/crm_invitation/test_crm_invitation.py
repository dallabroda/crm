# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now


class TestCRMInvitation(FrappeTestCase):
	def make_invitation(self, email="invitee@example.com", role="Sales User"):
		"""Create a Pending invitation without actually sending an email."""
		with patch.object(frappe, "sendmail"):
			return frappe.get_doc(
				doctype="CRM Invitation",
				email=email,
				role=role,
			).insert(ignore_permissions=True)

	def age(self, invitation, days):
		"""Pretend the invitation (and its last e-mail) went out `days` ago."""
		frappe.db.set_value(
			"CRM Invitation",
			invitation.name,
			{"creation": add_days(now(), -days), "email_sent_at": add_days(now(), -days)},
			update_modified=False,
		)
		invitation.reload()

	def test_new_invitation_is_pending_with_key(self):
		invitation = self.make_invitation()
		self.assertEqual(invitation.status, "Pending")
		self.assertTrue(invitation.key)
		self.assertEqual(invitation.invited_by, frappe.session.user)

	def test_accept_pending_invitation(self):
		invitation = self.make_invitation()

		invitation.accept()

		self.assertEqual(invitation.status, "Accepted")
		self.assertTrue(invitation.accepted_at)
		self.assertTrue(frappe.db.exists("User", invitation.email))

	def test_accept_clears_key(self):
		"""The key is wiped after acceptance so the invite link cannot be reused."""
		invitation = self.make_invitation()

		invitation.accept()

		self.assertIsNone(invitation.key)
		self.assertFalse(frappe.db.get_value("CRM Invitation", invitation.name, "key"))

	def test_accept_already_accepted_raises(self):
		"""An already-accepted invitation cannot be accepted again."""
		invitation = self.make_invitation()
		invitation.accept()

		invitation.reload()
		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_expired_invitation_raises(self):
		invitation = self.make_invitation()
		invitation.status = "Expired"
		invitation.save(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			invitation.accept()

	def test_accept_reports_newly_created_user(self):
		invitation = self.make_invitation(email="brand-new@example.com")

		self.assertTrue(invitation.accept())
		self.assertEqual(frappe.db.get_value("User", invitation.email, "default_app"), "crm")

	def test_accept_reports_existing_user(self):
		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="already-there@example.com",
			send_welcome_email=0,
			first_name="Already There",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="already-there@example.com")

		self.assertFalse(invitation.accept())

	def test_accept_invitation_sends_new_user_to_set_password(self):
		"""A new user must set a password instead of being logged in directly."""
		from crm.api import accept_invitation

		invitation = self.make_invitation(email="new-invitee@example.com")

		accept_invitation(key=invitation.key)

		self.assertEqual(frappe.local.response["type"], "redirect")
		self.assertIn("/update-password?key=", frappe.local.response["location"])

	def test_accept_invitation_logs_in_existing_user(self):
		"""An existing user already has a password, so log them straight in."""
		from crm.api import accept_invitation

		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="existing-invitee@example.com",
			send_welcome_email=0,
			first_name="Existing Invitee",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="existing-invitee@example.com")

		with patch.object(frappe.local, "login_manager", create=True) as login_manager:
			accept_invitation(key=invitation.key)

		login_manager.login_as.assert_called_once_with("existing-invitee@example.com")
		self.assertEqual(frappe.local.response["location"], "/crm")

	def test_desk_accept_mails_new_user_a_set_password_link(self):
		invitation = self.make_invitation(email="desk-invitee@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_called_once()

	def test_desk_accept_does_not_mail_existing_user(self):
		frappe.get_doc(
			doctype="User",
			user_type="System User",
			email="desk-existing@example.com",
			send_welcome_email=0,
			first_name="Desk Existing",
		).insert(ignore_permissions=True)
		invitation = self.make_invitation(email="desk-existing@example.com")

		with patch("frappe.core.doctype.user.user.User.send_welcome_mail_to_user") as welcome_mail:
			invitation.accept_invitation()

		welcome_mail.assert_not_called()

	def test_expire_invitations_expires_old_pending_invites(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import expire_invitations

		invitation = self.make_invitation(email="stale@example.com")
		# valid for INVITATION_DAYS from the last e-mail
		self.age(invitation, 4)

		expire_invitations()

		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Expired")

	def test_accept_grants_role_to_user(self):
		invitation = self.make_invitation(email="manager@example.com", role="Sales Manager")

		invitation.accept()

		user = frappe.get_doc("User", invitation.email)
		user_roles = {r.role for r in user.roles}
		self.assertIn("Sales Manager", user_roles)
		self.assertIn("Sales User", user_roles)

	# Pending invitations screen (credtech#190)

	def test_list_shows_who_invited_and_until_when(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import INVITATION_DAYS, get_invitations

		invitation = self.make_invitation(email="listed@example.com")
		row = next(r for r in get_invitations() if r.name == invitation.name)
		self.assertEqual(row.invited_by, frappe.session.user)
		self.assertTrue(row.invited_by_name)
		self.assertFalse(row.expired)
		self.assertEqual(
			frappe.utils.getdate(row.valid_until),
			frappe.utils.getdate(add_days(row.sent_on, INVITATION_DAYS)),
		)

	def test_resend_pending_sends_again_and_renews(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import resend_invitation

		invitation = self.make_invitation(email="again@example.com")
		self.age(invitation, 2)
		with patch.object(frappe, "sendmail") as mail:
			self.assertEqual(resend_invitation(invitation.name), invitation.name)
		mail.assert_called_once()
		self.assertEqual(mail.call_args.kwargs["template"], "crm_invitation")
		invitation.reload()
		self.assertGreater(
			invitation.valid_until(), frappe.utils.now_datetime() + frappe.utils.datetime.timedelta(days=2)
		)

	def test_resend_expired_makes_a_new_invitation(self):
		from crm.fcrm.doctype.crm_invitation.crm_invitation import expire_invitations, resend_invitation

		invitation = self.make_invitation(email="late@example.com")
		self.age(invitation, 5)
		expire_invitations()
		with patch.object(frappe, "sendmail"):
			renewed = resend_invitation(invitation.name)
		self.assertNotEqual(renewed, invitation.name)
		self.assertFalse(frappe.db.exists("CRM Invitation", invitation.name))
		self.assertEqual(
			frappe.db.get_value("CRM Invitation", renewed, ["email", "status"]),
			("late@example.com", "Pending"),
		)

	def test_old_link_does_not_get_in_before_the_daily_job(self):
		invitation = self.make_invitation(email="oldlink@example.com")
		self.age(invitation, 4)
		with self.assertRaises(frappe.ValidationError):
			invitation.accept()
		self.assertEqual(frappe.db.get_value("CRM Invitation", invitation.name, "status"), "Expired")

	def test_inviting_again_replaces_an_expired_invitation(self):
		from crm.api import invite_by_email
		from crm.fcrm.doctype.crm_invitation.crm_invitation import expire_invitations

		invitation = self.make_invitation(email="replaced@example.com")
		self.age(invitation, 5)
		expire_invitations()
		with patch.object(frappe, "sendmail"):
			result = invite_by_email("replaced@example.com", "Sales User")
		self.assertEqual(result["to_invite"], ["replaced@example.com"])
		self.assertFalse(frappe.db.exists("CRM Invitation", invitation.name))
		self.assertTrue(
			frappe.db.exists("CRM Invitation", {"email": "replaced@example.com", "status": "Pending"})
		)
