"""Zenvia Voz adapter (credtech#272), the former TotalVoice: click-to-call and calls recorded from webhooks.

Reference: https://totalvoice.github.io/totalvoice-docs/ (Zenvia kept the TotalVoice API; base URL
https://voice-api.zenvia.com, header `Access-Token`).

- Click-to-call: `POST /chamada` with `numero_origem` (the salesperson: their phone in +E.164 or their
  Zenvia extension) and `numero_destino` (the customer). Zenvia rings the salesperson first, then the
  customer, and records with `gravar_audio`. The CRM's call id and the deal go in `tags`, which comes back.
- Calls: Zenvia posts "Chamada - Fim" at the end of every call (click-to-call and calls made from an
  extension) and "DID - Fim de Chamada" at the end of every call received on the company's numbers. Zenvia
  has no API to register them on the company's own account: the settings screen shows the two addresses
  to paste in the Zenvia panel (Desenvolvedores > Configurações da API). The DID address carries `tipo=did`.
- Both bodies have the call's `id`, `url_gravacao`, `tags` and two legs, `origem` and `destino`, each with
  `numero`, `tipo` (ramal, movel, fixo), `status`, `data_inicio` and durations.

Not run against a real account yet: the test account is the owner's, at the end of credtech#272.
"""

import json
import re
from datetime import datetime, timedelta, timezone

import frappe
import requests
from frappe import _
from frappe.utils import cint
from frappe.utils.data import convert_utc_to_system_timezone

from crm.integrations.voip.base import Operator

API_URL = "https://voice-api.zenvia.com"
WEBHOOK_PATH = "/api/method/crm.integrations.voip.webhook.zenvia"

# Status of a leg (`origem`/`destino`) in the doc to CRM Call Log status
LEG_STATUS = {
	"atendida": "Completed",
	"sem resposta": "No Answer",
	"ocupado": "Busy",
	"cancelada": "Canceled",
	"congestionado": "Failed",
	"falha": "Failed",
	"não existe": "Failed",
}

E164 = re.compile(r"\+[1-9]\d{7,14}")
EXTENSION = re.compile(r"\d{2,6}")


class Zenvia(Operator):
	key = "zenvia"
	medium = "Zenvia"
	settings_doctype = "CRM Zenvia Settings"

	def validate_extension(self, extension: str):
		"""Zenvia rings first the salesperson's extension in the Zenvia panel or their phone."""
		if not (EXTENSION.fullmatch(extension or "") or E164.fullmatch(extension or "")):
			frappe.throw(
				_(
					"Use the salesperson's Zenvia extension (2 to 6 digits) or their phone in international format (+5548999990000)."
				)
			)

	def is_call_event(self, payload: dict) -> bool:
		return (
			bool(payload.get("id"))
			and isinstance(payload.get("origem"), dict)
			and isinstance(payload.get("destino"), dict)
		)

	def parse_webhook(self, payload: dict) -> dict:
		received = bool(frappe.request) and frappe.request.args.get("tipo") == "did"
		return parse_call(payload, received)

	def originate_call(self, settings, extension: str, number: str, deal: str | None) -> str | None:
		return originate_call(settings, extension, number, deal)


def originate_call(settings, extension: str, number: str, deal: str | None) -> str | None:
	"""POST /chamada: the salesperson (leg A) is rung first, the customer (leg B) when they answer."""
	body = {
		"numero_origem": extension,
		"numero_destino": to_e164(number),
		"gravar_audio": True,
		"tags": json.dumps({"crm": "zenvia", "deal": deal}, separators=(",", ":")),
	}
	if settings.caller_number:
		body["bina_destino"] = settings.caller_number
	response = _request(settings, "post", "/chamada", json=body)
	if response.status_code >= 400 or not _succeeded(response):
		frappe.log_error(
			title="Zenvia: click-to-call refused",
			message=f"HTTP {response.status_code}: {response.text[:500]}",
		)
		frappe.throw(call_error(response))
	call_id = (response.json().get("dados") or {}).get("id")
	return f"zenvia-{call_id}" if call_id else None


def call_error(response) -> str:
	if response.status_code in (401, 403):
		return _("Zenvia refused the access token. Check it in the telephony settings.")
	if response.status_code == 429:
		return _("Too many calls in a minute. Wait a moment and try again.")
	try:
		message = response.json().get("mensagem")
	except ValueError:
		message = None
	if message:
		return _("Zenvia refused the call: {0}").format(message)
	return _("Zenvia refused the call (HTTP {0}).").format(response.status_code)


def parse_call(payload: dict, received: bool) -> dict:
	"""A "Chamada - Fim" or "DID - Fim de Chamada" body in the common call format."""
	origin, target = payload.get("origem") or {}, payload.get("destino") or {}
	tags = read_tags(payload.get("tags"))

	if received:
		# a call to the company's number: the salesperson is the extension leg, the customer the other one
		agent, customer = (origin, target) if origin.get("tipo") == "ramal" else (target, origin)
		status = LEG_STATUS.get(agent.get("status") or customer.get("status"), "Failed")
		leg = agent if agent.get("data_inicio") else customer
	else:
		agent, customer = origin, target
		# the salesperson never answered: the customer was never called
		if origin.get("status") not in (None, "atendida") and not target.get("status"):
			status = "Canceled"
		else:
			status = LEG_STATUS.get(target.get("status"), "Failed")
		leg = target

	start = to_system_time(leg.get("data_inicio") or payload.get("data_criacao"))
	return {
		"id": f"zenvia-{payload['id']}",
		"type": "Incoming" if received else "Outgoing",
		"extension": agent.get("numero"),
		"number": customer.get("numero"),
		"status": status,
		"start_time": start,
		"end_time": (start + timedelta(seconds=cint(leg.get("duracao_segundos")))) if start else None,
		"duration": cint(leg.get("duracao_falada_segundos")),
		"recording_url": payload.get("url_gravacao") or None,
		"deal": tags.get("deal"),
	}


def read_tags(value) -> dict:
	"""The CRM's own `tags` (JSON); anything else someone typed there is ignored."""
	try:
		tags = json.loads(value) if value else {}
	except (TypeError, ValueError):
		return {}
	return tags if isinstance(tags, dict) and tags.get("crm") == "zenvia" else {}


def check_token(settings):
	"""GET /saldo: the cheapest call that needs a valid token."""
	response = _request(settings, "get", "/saldo")
	if response.status_code in (401, 403) or (response.status_code < 400 and not _succeeded(response)):
		frappe.throw(_("Zenvia refused the access token. Check that it was copied whole."))
	if response.status_code >= 400:
		frappe.throw(_("Zenvia refused the settings (HTTP {0}).").format(response.status_code))


def webhook_urls(settings) -> dict:
	"""The two addresses the company pastes in the Zenvia panel; the secret goes in them."""
	secret = settings.get_password("webhook_secret", raise_exception=False)
	if not secret:
		return {}
	base = frappe.utils.get_url(f"{WEBHOOK_PATH}?key={secret}")
	return {"chamada_fim": base, "did_fim": f"{base}&tipo=did"}


def to_e164(number: str) -> str:
	"""Zenvia's doc asks for +E.164. A Brazilian number without the country code (DDD + number) gets +55."""
	digits = re.sub(r"\D", "", number or "")
	if (number or "").strip().startswith("+"):
		return "+" + digits
	if len(digits) in (10, 11):
		return "+55" + digits
	return "+" + digits


def to_system_time(value: str | None):
	"""Zenvia sends ISO 8601 with offset ("2019-09-06T11:19:11-03:00"); the call log keeps system time."""
	if not value:
		return None
	try:
		moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
	except ValueError:
		return None
	if moment.tzinfo:
		moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
		return convert_utc_to_system_timezone(moment).replace(tzinfo=None)
	return moment


def _succeeded(response) -> bool:
	try:
		return bool(response.json().get("sucesso"))
	except ValueError:
		return False


def _request(settings, method: str, path: str, **kwargs):
	try:
		return requests.request(
			method,
			f"{API_URL}{path}",
			headers={"Access-Token": settings.get_password("access_token"), "Accept": "application/json"},
			timeout=20,
			**kwargs,
		)
	except requests.RequestException:
		frappe.log_error(title="Zenvia: could not reach the API")
		frappe.throw(_("Could not reach Zenvia. Please try again in a few minutes."))
