import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

import frappe
import requests
from frappe import _
from frappe.query_builder import Order
from pypika.functions import Replace
from werkzeug.wrappers import Response

from crm.utils import get_default_phone_country, is_same_phone_number, parse_phone_number


def _get_recording_credentials(telephony_medium: str) -> tuple | None:
	"""Return (api_key, secret) for the given telephony medium, or None when the
	recording needs no auth.

	A manual/unrecognized medium (a recording added by hand) is fetched as-is, and
	a provider whose credentials aren't configured yet falls back to no auth rather
	than raising — so the proxy attempts the fetch and lets the provider decide,
	instead of 500-ing before the request is even made.
	"""
	if telephony_medium == "Twilio":
		s = frappe.get_single("CRM Twilio Settings")
		secret = s.get_password("api_secret", raise_exception=False)
		return (s.api_key, secret) if s.api_key and secret else None
	elif telephony_medium == "Exotel":
		s = frappe.get_single("CRM Exotel Settings")
		token = s.get_password("api_token", raise_exception=False)
		return (s.api_key, token) if s.api_key and token else None
	from crm.integrations.voip.operators import get_operator_by_medium

	# API4Com: recordUrl is a plain link in their doc; whether it ever asks for the token is credtech#100
	operator = get_operator_by_medium(telephony_medium)
	if operator:
		return operator.recording_auth(operator.get_settings())
	# manual or unrecognized medium: no provider auth to apply
	return None


@frappe.whitelist()
def is_call_integration_enabled():
	from crm.integrations.voip.api import callable_operators

	# operators the CRM places calls through on the server (credtech#268), by key: {"api4com": "API4Com"}
	voip = {operator.key: operator.medium for operator in callable_operators()}
	return {
		"integrations": {
			"twilio": bool(frappe.db.get_single_value("CRM Twilio Settings", "enabled")),
			"exotel": bool(frappe.db.get_single_value("CRM Exotel Settings", "enabled")),
			**{key: True for key in voip},
		},
		"voip": voip,
		"default_calling_medium": get_user_default_calling_medium(),
	}


def get_user_default_calling_medium():
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		return None

	default_medium = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")

	if not default_medium:
		return None

	return default_medium


@frappe.whitelist()
def set_default_calling_medium(medium: str):
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": medium,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("CRM Telephony Agent", frappe.session.user, "default_medium", medium)

	return get_user_default_calling_medium()


@frappe.whitelist()
def add_note_to_call_log(call_sid: str, note: dict):
	"""Add/Update note to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_note = None
	if not note.get("name"):
		_note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": note.get("title", "Call Note"),
				"content": note.get("content"),
			}
		).insert(ignore_permissions=True)
	else:
		_note = frappe.set_value("FCRM Note", note.get("name"), "content", note.get("content"))

	call_log = frappe.get_cached_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", _note.name)
	call_log.save(ignore_permissions=True)

	return _note


@frappe.whitelist()
def add_task_to_call_log(call_sid: str, task: dict):
	"""Add/Update task to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_task = None
	if not task.get("name"):
		_task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		).insert(ignore_permissions=True)
	else:
		_task = frappe.get_doc("CRM Task", task.get("name"))
		_task.update(
			{
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		)
		_task.save(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)

	return _task


@frappe.whitelist()
def get_contact_lead_or_deal_from_number(number: str):
	"""The most recent open deal of the number's contact, else the contact itself."""
	contact = get_contact_by_phone_number(number)
	if contact.get("deal"):
		return contact.get("deal"), "CRM Deal"
	if contact.get("name"):
		return contact.get("name"), "Contact"
	return None, None


def link_call_log_to_number(call_log, phone_number: str) -> dict:
	"""Link the call to every open deal of the number's contact, or to the contact when it
	has none. Returns the lookup result so callers can act on a number nobody has."""
	contact = get_contact_by_phone_number(phone_number)
	for deal in contact.get("deals") or []:
		call_log.link_with_reference_doc("CRM Deal", deal)
	if contact.get("name") and not contact.get("deals"):
		call_log.link_with_reference_doc("Contact", contact.get("name"))
	return contact


@frappe.whitelist()
def get_contact_by_phone_number(phone_number: str):
	"""Get contact by phone number."""
	default_country = get_default_phone_country()
	number = parse_phone_number(phone_number, default_country)
	if number.get("is_valid"):
		# a number with its own country code (+1 ...) is read in that country
		return get_contact(phone_number, number.get("country"))
	return get_contact(phone_number, default_country, exact_match=True)


def _resolve_validated_ip(hostname: str, port: int) -> str:
	# Refuse any host that resolves to a non-public address (cloud metadata, localhost,
	# private/link-local ranges) and return a single validated IP to connect to. Returning
	# the exact resolved IP — rather than re-resolving at connect time — is what closes the
	# DNS-rebinding TOCTOU window.
	try:
		addrinfos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
	except socket.gaierror:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	ips = [info[4][0] for info in addrinfos]
	if not ips:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	for ip in ips:
		if not ipaddress.ip_address(ip).is_global:
			frappe.throw(_("Recording URL is not allowed"), frappe.ValidationError)

	return ips[0]


class _PinnedIPAdapter(requests.adapters.HTTPAdapter):
	# Connect to a pre-validated IP while keeping the original hostname for the Host header,
	# TLS SNI and certificate verification. The socket therefore reaches the exact IP that was
	# checked, so DNS can't be rebound to an internal address between check and connect.
	def __init__(self, pinned_ip: str, hostname: str, **kwargs):
		self._pinned_ip = pinned_ip
		self._hostname = hostname
		super().__init__(**kwargs)

	def send(self, request, **kwargs):
		parsed = urlparse(request.url)
		literal_ip = (
			f"[{self._pinned_ip}]" if ipaddress.ip_address(self._pinned_ip).version == 6 else self._pinned_ip
		)
		netloc = f"{literal_ip}:{parsed.port}" if parsed.port else literal_ip
		request.url = urlunparse(parsed._replace(netloc=netloc))
		host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
		request.headers["Host"] = f"{host}:{parsed.port}" if parsed.port else host
		if parsed.scheme == "https":
			self.poolmanager.connection_pool_kw["server_hostname"] = self._hostname
			self.poolmanager.connection_pool_kw["assert_hostname"] = self._hostname
		return super().send(request, **kwargs)


def _safe_get(url: str, auth, headers: dict):
	# TODO: this SSRF-safe fetch (host validation + IP pinning) will likely need to be shared
	# with domain enrichment; until that feature ships, this local helper is the interim workaround.
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https") or not parsed.hostname:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	port = parsed.port or (443 if parsed.scheme == "https" else 80)
	pinned_ip = _resolve_validated_ip(parsed.hostname, port)

	session = requests.Session()
	session.mount(f"{parsed.scheme}://", _PinnedIPAdapter(pinned_ip, parsed.hostname))
	resp = session.get(url, auth=auth, headers=headers, stream=True, timeout=30, allow_redirects=False)
	return resp, session


def _fetch_recording(url: str, auth, headers: dict):
	# Follow redirects manually so every hop is validated and IP-pinned: a provider URL can
	# 302 to a signed CDN URL (legitimate), but without per-hop checks a redirect to an
	# internal address would bypass validation. Provider credentials are dropped after the
	# first hop so they aren't leaked to the redirect target.
	current_url = url
	current_auth = auth
	for _hop in range(5):
		resp, session = _safe_get(current_url, current_auth, headers)
		if resp.is_redirect and resp.headers.get("Location"):
			current_url = requests.compat.urljoin(current_url, resp.headers["Location"])
			current_auth = None
			resp.close()
			session.close()
			continue
		resp._pinned_session = session
		return resp

	frappe.throw(_("Too many redirects while fetching recording"), frappe.ValidationError)


@frappe.whitelist()
def get_recording_url(call_log_name: str):
	"""Proxy a call recording (authenticating with the provider) so it plays in the browser.

	Forwards the browser's Range request to the provider and passes the response back with
	Accept-Ranges/Content-Length set. Without range support the HTML <audio> element can't
	read the recording's duration (shows 0:00) or seek within it.
	"""
	if not call_log_name or not frappe.db.exists("CRM Call Log", call_log_name):
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	log = frappe.get_doc("CRM Call Log", call_log_name)
	log.check_permission("read")

	if not log.recording_url:
		frappe.throw(_("Recording URL not found"), frappe.DoesNotExistError)

	auth = _get_recording_credentials(log.telephony_medium)
	# forward the browser's Range header so the provider (Twilio/Exotel CDN) can return
	# just the requested bytes; falls back to the full file if it doesn't support ranges
	req_headers = {}
	range_header = frappe.get_request_header("Range")
	if range_header:
		req_headers["Range"] = range_header

	# stream instead of buffering the whole file: the provider's Content-Length reaches
	# the browser immediately so the <audio> element can show the duration right away,
	# rather than waiting for the entire recording to download server-side first
	upstream = _fetch_recording(log.recording_url, auth, req_headers)
	upstream.raise_for_status()

	def _stream():
		try:
			yield from upstream.iter_content(chunk_size=64 * 1024)
		finally:
			upstream.close()
			session = getattr(upstream, "_pinned_session", None)
			if session is not None:
				session.close()

	response = Response(
		_stream(),
		status=upstream.status_code,
		mimetype=upstream.headers.get("Content-Type") or "audio/mpeg",
	)
	response.headers["Accept-Ranges"] = "bytes"
	for header in ("Content-Length", "Content-Range"):
		if upstream.headers.get(header):
			response.headers[header] = upstream.headers[header]
	return response


def get_contact(phone_number: str, country: str | None = None, exact_match: bool = False):
	"""The contact that has this number, with its open deals (most recently modified first).

	`deal` is the most recent open deal and `deals` all of them: a call or message from
	the number belongs on every deal still open for that person. Closed deals are left out.
	"""
	if not phone_number:
		return {"mobile_no": phone_number}

	country = country or get_default_phone_country()
	digits = "".join(c for c in phone_number if c.isdigit())
	if not digits:
		return {"mobile_no": phone_number}

	# Pre-filter on the last 8 digits: they survive every format (country code, DDD,
	# trunk prefix, with or without the mobile 9). The exact match is confirmed below.
	# Search all of a contact's numbers (phone_nos child table) and not just the
	# primary mobile_no, so calls from a secondary number still resolve.
	Contact = frappe.qb.DocType("Contact")
	ContactPhone = frappe.qb.DocType("Contact Phone")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(ContactPhone.phone, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(ContactPhone)
		.join(Contact)
		.on(ContactPhone.parent == Contact.name)
		.select(
			Contact.name,
			Contact.full_name,
			Contact.image,
			Contact.mobile_no,
			ContactPhone.phone.as_("matched_phone"),
		)
		.where(ContactPhone.parenttype == "Contact")
		.where(normalized_phone.like(f"%{digits[-8:]}%"))
		.orderby(Contact.modified, order=Order.desc)
	)
	contacts = [
		contact
		for contact in query.run(as_dict=True)
		if is_same_phone_number(contact.matched_phone, phone_number, country, validate=not exact_match)
	]
	if not contacts:
		return {"mobile_no": phone_number}

	contact = contacts[0]
	deals = get_open_deals_of_contacts(list(dict.fromkeys(c.name for c in contacts)))
	if deals:
		contact["deal"] = deals[0]
		contact["deals"] = deals
	return contact


def get_open_deals_of_contacts(contacts: list[str]) -> list[str]:
	"""Deals not yet won or lost that list any of the contacts, most recently modified first."""
	Deal = frappe.qb.DocType("CRM Deal")
	DealContact = frappe.qb.DocType("CRM Contacts")
	Status = frappe.qb.DocType("CRM Deal Status")
	query = (
		frappe.qb.from_(Deal)
		.join(DealContact)
		.on((DealContact.parent == Deal.name) & (DealContact.parenttype == "CRM Deal"))
		.left_join(Status)
		.on(Status.name == Deal.status)
		.select(Deal.name, Deal.modified)
		.distinct()
		.where(DealContact.contact.isin(contacts))
		.where(Status.type.isnull() | Status.type.notin(["Won", "Lost"]))
		.orderby(Deal.modified, order=Order.desc)
	)
	return [row.name for row in query.run(as_dict=True)]
