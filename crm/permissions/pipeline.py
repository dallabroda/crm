# Copyright (c) 2026, CredTech Digital and contributors
# For license information, please see license.txt
"""Who sees which pipelines and cards.

- Admin (Administrator, System Manager, or Sales Manager outside the sales hierarchy): every
  pipeline and every card.
- Pipeline owner (member with role Owner): every card of that pipeline.
- Member: only pipelines they belong to, and in them only the cards they own or are assigned to
  (plus their team's, when the sales hierarchy is enabled).
"""

import frappe
from frappe import _
from frappe.query_builder import Criterion

from crm.permissions.org_hierarchy import _in_hierarchy, _team_mem_query, hierarchy_enabled

PIPELINE_OWNER_ROLE = "Pipeline Owner"


def is_admin(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return True
	# Same rule as the sales hierarchy: a Sales Manager placed in the tree only sees their team
	return "Sales Manager" in roles and not (hierarchy_enabled() and _in_hierarchy(user))


def _member_pipelines(user: str, role: str | None = None):
	Member = frappe.qb.DocType("CRM Pipeline Member").as_("_pm")
	query = (
		frappe.qb.from_(Member)
		.select(Member.parent)
		.where((Member.parenttype == "CRM Pipeline") & (Member.user == user))
	)
	if role:
		query = query.where(Member.role == role)
	return query


def deal_conditions(user: str | None = None):
	"""Query Builder criterion for the cards `user` can see; None means no restriction."""
	user = user or frappe.session.user
	if is_admin(user):
		return None

	Deal = frappe.qb.DocType("CRM Deal")
	Todo = frappe.qb.DocType("ToDo").as_("_todo")
	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	owners = [Deal.deal_owner == user]
	assignees = Todo.allocated_to == user
	if in_tree:
		owners.append(Deal.deal_owner.isin(_team_mem_query(user)))
		assignees = assignees | Todo.allocated_to.isin(_team_mem_query(user))

	assigned = Deal.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where((Todo.reference_type == "CRM Deal") & (Todo.status != "Cancelled") & assignees)
	)
	own_or_assigned = Criterion.any([*owners, assigned])
	owned_pipeline = Deal.pipeline.isin(_member_pipelines(user, "Owner"))
	return Deal.pipeline.isin(_member_pipelines(user)) & (owned_pipeline | own_or_assigned)


def get_deal_permission_query_conditions(user=None):
	cond = deal_conditions(user)
	return _sql(cond)


def has_deal_permission(doc, ptype, user):
	user = user or frappe.session.user
	if is_admin(user):
		return True
	if ptype == "create" or not doc.name or doc.is_new():
		# Creation is checked in CRM Deal.validate, where the pipeline is known
		return True
	Deal = frappe.qb.DocType("CRM Deal")
	return bool(
		frappe.qb.from_(Deal)
		.select(Deal.name)
		.where(Deal.name == doc.name)
		.where(deal_conditions(user))
		.limit(1)
		.run()
	)


def validate_assignment(doc, method=None):
	"""ToDo hook: cards are only assigned to people who take part in their pipeline (an assignment
	also shares the card, which would expose it outside the pipeline)."""
	if doc.reference_type != "CRM Deal" or not doc.reference_name or not doc.allocated_to:
		return
	if doc.status == "Cancelled" or not (doc.is_new() or doc.has_value_changed("allocated_to")):
		return
	pipeline = frappe.db.get_value("CRM Deal", doc.reference_name, "pipeline")
	if pipeline and not get_role_in_pipeline(pipeline, doc.allocated_to):
		frappe.throw(
			_("{0} is not a member of this pipeline and cannot be assigned to the card.").format(
				frappe.bold(frappe.utils.get_fullname(doc.allocated_to))
			)
		)


def get_pipeline_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if is_admin(user):
		return ""
	Pipeline = frappe.qb.DocType("CRM Pipeline")
	return _sql(Pipeline.name.isin(_member_pipelines(user)))


def has_pipeline_permission(doc, ptype, user):
	user = user or frappe.session.user
	if is_admin(user):
		return True
	if ptype == "create" or doc.is_new():
		return PIPELINE_OWNER_ROLE in frappe.get_roles(user)
	role = get_member_role(doc.name, user)
	if ptype == "read":
		return bool(role)
	return role == "Owner"


def get_stage_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if is_admin(user):
		return ""
	Stage = frappe.qb.DocType("CRM Deal Status")
	return _sql(Stage.pipeline.isin(_member_pipelines(user)))


def has_stage_permission(doc, ptype, user):
	user = user or frappe.session.user
	if is_admin(user):
		return True
	role = get_member_role(doc.pipeline, user) if doc.pipeline else None
	if ptype == "read":
		return bool(role)
	return role == "Owner"


def get_member_role(pipeline: str, user: str | None = None) -> str | None:
	return frappe.db.get_value(
		"CRM Pipeline Member",
		{"parenttype": "CRM Pipeline", "parent": pipeline, "user": user or frappe.session.user},
		"role",
	)


def get_role_in_pipeline(pipeline: str, user: str | None = None) -> str | None:
	"""Admin, Owner or Member; None when the user does not take part in the pipeline."""
	user = user or frappe.session.user
	return "Admin" if is_admin(user) else get_member_role(pipeline, user)


def _sql(cond) -> str:
	return cond.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if cond else ""
