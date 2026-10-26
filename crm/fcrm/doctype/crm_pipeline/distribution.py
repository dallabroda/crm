"""Who gets a card that arrives on its own (ads, web forms, e-mail, calls) — credtech#51.

Owner decision (26/10/2026): each pipeline chooses, in its `distribution` setting
	{mode: "round_robin" | "rules", round_robin_users: [user], rules: [{field, value, user}],
	 fallback: "round_robin" | "owner"}
- round_robin: one card for each salesperson in turn (round_robin_users, or every pipeline member with
  the Member role when empty);
- rules: the first rule whose field equals the value (case and surrounding spaces ignored) decides;
  with no match, the fallback applies.
Users who left the pipeline are skipped; with nobody left, the card goes to the pipeline owner.
"""

import json

import frappe

DEFAULT = {"mode": "round_robin", "round_robin_users": [], "rules": [], "fallback": "round_robin"}


def load(raw) -> dict:
	try:
		value = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
	except ValueError:
		value = {}
	return normalize(value)


def normalize(value: dict) -> dict:
	value = value if isinstance(value, dict) else {}
	mode = value.get("mode") if value.get("mode") in ("round_robin", "rules") else "round_robin"
	fallback = value.get("fallback") if value.get("fallback") in ("round_robin", "owner") else "round_robin"
	users = [u for u in value.get("round_robin_users") or [] if isinstance(u, str) and u]
	rules = [
		{"field": str(r.get("field")), "value": str(r.get("value")), "user": str(r.get("user"))}
		for r in value.get("rules") or []
		if isinstance(r, dict) and r.get("field") and r.get("value") not in (None, "") and r.get("user")
	]
	return {"mode": mode, "round_robin_users": users, "rules": rules, "fallback": fallback}


def _members(pipeline) -> dict:
	"""{user: role} of the pipeline's enabled members, in their order."""
	rows = frappe.get_all(
		"CRM Pipeline Member",
		filters={"parent": pipeline, "parenttype": "CRM Pipeline"},
		fields=["user", "role"],
		order_by="idx asc",
	)
	enabled = set(
		frappe.get_all("User", {"name": ("in", [r.user for r in rows] or [""]), "enabled": 1}, pluck="name")
	)
	return {r.user: r.role for r in rows if r.user in enabled}


def _matches(value, expected) -> bool:
	return str(value if value is not None else "").strip().casefold() == str(expected).strip().casefold()


def _round_robin(pipeline, candidates):
	"""Next salesperson after the last one served, under a database lock (leads arrive together)."""
	lock = f"crm_distribution:{pipeline}"[:64]
	frappe.db.sql("SELECT GET_LOCK(%s, 10)", lock)
	try:
		last = frappe.db.get_value("CRM Pipeline", pipeline, "last_assigned")
		position = candidates.index(last) + 1 if last in candidates else 0
		chosen = candidates[position % len(candidates)]
		frappe.db.set_value("CRM Pipeline", pipeline, "last_assigned", chosen, update_modified=False)
		return chosen
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", lock)


def pick_salesperson(pipeline: str, values: dict) -> str | None:
	"""Salesperson for a new card of `pipeline`; `values` are the fields of the incoming entry."""
	settings = load(frappe.db.get_value("CRM Pipeline", pipeline, "distribution"))
	members = _members(pipeline)
	owners = [u for u, role in members.items() if role == "Owner"]
	owner = owners[0] if owners else None

	if settings["mode"] == "rules":
		for rule in settings["rules"]:
			if rule["user"] in members and _matches(values.get(rule["field"]), rule["value"]):
				return rule["user"]
		if settings["fallback"] == "owner":
			return owner

	candidates = [u for u in settings["round_robin_users"] if u in members] or [
		u for u, role in members.items() if role == "Member"
	]
	if candidates:
		return _round_robin(pipeline, candidates)
	return owner
