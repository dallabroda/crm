"""Zenvia Voz adapter (credtech#272): click-to-call by POST /chamada, calls from the "Chamada - Fim" and
"DID - Fim de Chamada" webhooks (bodies as in the TotalVoice/Zenvia doc). Not run against a real account."""

import json
from unittest.mock import MagicMock, patch

import frappe
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.integrations.voip import webhook, zenvia
from crm.integrations.voip.operators import get_operator, get_operator_by_medium
from crm.tests import CRMTestCase as FrappeTestCase
from crm.tests.test_voip_api4com import make_deal

SECRET = "zenvia-secret-for-tests"


def leg(numero, tipo, status, falada=0, total=0, inicio=None):
	return {
		"data_inicio": inicio,
		"numero": numero,
		"tipo": tipo,
		"status": status,
		"duracao_segundos": total,
		"duracao": "00:00:00",
		"duracao_cobrada_segundos": 0,
		"duracao_cobrada": "00:00:00",
		"duracao_falada_segundos": falada,
		"duracao_falada": "00:00:00",
		"preco": 0,
		"motivo_desconexao": "16. normal",
	}


def chamada_fim(call_id=37721262, tags=None, origem=None, destino=None, **overrides):
	"""The "Chamada - Fim" example of the doc, with the CRM's tags when it placed the call."""
	return {
		"id": call_id,
		"data_criacao": "2019-09-06T11:19:11-03:00",
		"ativa": False,
		"url_gravacao": "https://api.evoline.com.br/rec/?id=37721262&x=7a8718b28b&cid=2150",
		"cliente_id": 2150,
		"conta_id": 2150,
		"ramal_id_origem": 62291,
		"tags": tags,
		"status_geral": "finalizada",
		"origem": origem
		or leg("4000", "ramal", "atendida", falada=20, total=30, inicio="2019-09-06T11:19:05-03:00"),
		"destino": destino
		or leg(
			"+5548988887777", "movel", "atendida", falada=14, total=24, inicio="2019-09-06T11:19:11-03:00"
		),
		"gravacoes_parciais": [],
		**overrides,
	}


def crm_tags(deal):
	return json.dumps({"crm": "zenvia", "deal": deal})


def response(status=200, body=None):
	mock = MagicMock(status_code=status, text=json.dumps(body or {}))
	mock.json.return_value = body or {}
	return mock


def settings():
	s = frappe.get_single("CRM Zenvia Settings")
	s.update({"enabled": 1, "access_token": "token-for-tests", "caller_number": "", "webhook_secret": SECRET})
	return s


class TestZenviaOperator(FrappeTestCase):
	def test_registered_and_originates_without_polling(self):
		op = get_operator("zenvia")
		self.assertIs(op, get_operator_by_medium("Zenvia"))
		self.assertTrue(op.can_originate)
		self.assertFalse(op.polls)

	def test_extension_is_a_zenvia_extension_or_a_phone(self):
		op = zenvia.Zenvia()
		for good in ("4000", "12", "+5548999990000"):
			op.validate_extension(good)
		for bad in ("1", "1234567", "48999990000", "ramal"):
			with self.subTest(bad=bad), self.assertRaises(frappe.ValidationError):
				op.validate_extension(bad)

	def test_only_call_bodies_are_events(self):
		op = zenvia.Zenvia()
		self.assertTrue(op.is_call_event(chamada_fim()))
		self.assertFalse(op.is_call_event({"id": 1, "mensagem": "saldo baixo"}))


class TestZenviaClickToCall(FrappeTestCase):
	def test_rings_the_salesperson_first_with_the_deal_in_tags(self):
		doc = settings()
		doc.caller_number = "+554830000000"
		ok = response(200, {"status": 200, "sucesso": True, "dados": {"id": 123123}})
		with patch("crm.integrations.voip.zenvia.requests.request", return_value=ok) as call:
			call_id = zenvia.originate_call(doc, "4000", "(48) 98888-7777", "CRM-DEAL-1")

		self.assertEqual(call_id, "zenvia-123123")
		method, url = call.call_args.args
		body = call.call_args.kwargs["json"]
		self.assertEqual((method, url), ("post", "https://voice-api.zenvia.com/chamada"))
		self.assertEqual(call.call_args.kwargs["headers"]["Access-Token"], "token-for-tests")
		self.assertEqual((body["numero_origem"], body["numero_destino"]), ("4000", "+5548988887777"))
		self.assertEqual((body["gravar_audio"], body["bina_destino"]), (True, "+554830000000"))
		self.assertEqual(zenvia.read_tags(body["tags"])["deal"], "CRM-DEAL-1")

	def test_refusal_shows_zenvias_reason(self):
		refused = response(400, {"status": 400, "sucesso": False, "mensagem": "saldo insuficiente"})
		with (
			patch("crm.integrations.voip.zenvia.requests.request", return_value=refused),
			self.assertRaises(frappe.ValidationError) as raised,
		):
			zenvia.originate_call(settings(), "4000", "48988887777", None)
		self.assertIn("saldo insuficiente", str(raised.exception))


class TestZenviaCalls(FrappeTestCase):
	def test_click_to_call_end(self):
		call = zenvia.parse_call(chamada_fim(tags=crm_tags("CRM-DEAL-1")), received=False)

		self.assertEqual(call["id"], "zenvia-37721262")
		self.assertEqual(
			(call["type"], call["status"], call["deal"]), ("Outgoing", "Completed", "CRM-DEAL-1")
		)
		self.assertEqual((call["extension"], call["number"]), ("4000", "+5548988887777"))
		self.assertEqual(call["duration"], 14)
		self.assertEqual((call["end_time"] - call["start_time"]).total_seconds(), 24)
		self.assertTrue(call["recording_url"].startswith("https://api.evoline.com.br/rec/"))

	def test_status_of_the_customer_leg(self):
		for status, expected in (("sem resposta", "No Answer"), ("ocupado", "Busy"), ("falha", "Failed")):
			with self.subTest(status=status):
				body = chamada_fim(destino=leg("+5548988887777", "movel", status))
				self.assertEqual(zenvia.parse_call(body, received=False)["status"], expected)

	def test_salesperson_not_answering_cancels_the_call(self):
		body = chamada_fim(
			origem=leg("4000", "ramal", "sem resposta"), destino=leg("+5548988887777", "movel", None)
		)
		self.assertEqual(zenvia.parse_call(body, received=False)["status"], "Canceled")

	def test_tags_typed_by_someone_else_are_ignored(self):
		self.assertEqual(zenvia.read_tags("cliente vip"), {})
		self.assertEqual(zenvia.read_tags(json.dumps({"deal": "X"})), {})
		self.assertIsNone(zenvia.parse_call(chamada_fim(tags="cliente vip"), received=False)["deal"])

	def test_received_call_puts_the_extension_and_the_customer_in_place(self):
		# the "DID - Fim de Chamada" example of the doc: the extension leg is the salesperson, whichever side it is
		body = chamada_fim(
			call_id=37721125,
			origem=leg("+5548988887777", "movel", "atendida", total=31, inicio="2019-09-06T11:18:19-03:00"),
			destino=leg("9998", "ramal", "atendida", falada=25, total=30, inicio="2019-09-06T11:18:20-03:00"),
		)
		call = zenvia.parse_call(body, received=True)

		self.assertEqual((call["type"], call["status"]), ("Incoming", "Completed"))
		self.assertEqual((call["extension"], call["number"]), ("9998", "+5548988887777"))
		self.assertEqual(call["duration"], 25)


class TestZenviaWebhook(FrappeTestCase):
	def setUp(self):
		frappe.db.set_single_value("System Settings", "country", "Brazil")
		with patch("crm.integrations.voip.zenvia.check_token"):
			settings().save()
		frappe.db.delete("CRM Telephony Extension", {"medium": "Zenvia"})
		if not frappe.db.exists("CRM Telephony Agent", "Administrator"):
			frappe.get_doc({"doctype": "CRM Telephony Agent", "user": "Administrator"}).insert()
		agent = frappe.get_doc("CRM Telephony Agent", "Administrator")
		agent.set_extension("Zenvia", "4000")
		agent.save()
		# the endpoint commits; keep everything inside the test transaction
		self.commit = patch.object(frappe.db, "commit")
		self.commit.start()

	def tearDown(self):
		self.commit.stop()
		frappe.local.request = None
		frappe.db.rollback()

	def post(self, payload, key=SECRET, tipo=None):
		query = {"key": key} if key is not None else {}
		if tipo:
			query["tipo"] = tipo
		builder = EnvironBuilder(
			method="POST",
			path="/api/method/crm.integrations.voip.webhook.zenvia",
			query_string=query or None,
			json=payload,
		)
		frappe.local.request = Request(builder.get_environ())
		return webhook.zenvia(**payload)

	def test_missing_or_wrong_secret_is_refused(self):
		for key in (None, "", "wrong"):
			with self.subTest(key=key), self.assertRaises(frappe.PermissionError):
				self.post(chamada_fim(), key=key)

	def test_click_to_call_lands_on_its_deal_in_the_salespersons_name(self):
		deal = make_deal("+55 48 98888-7777")

		self.post(chamada_fim(tags=crm_tags(deal)))

		log = frappe.get_doc("CRM Call Log", "zenvia-37721262")
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))
		self.assertEqual((log.type, log.status, log.telephony_medium), ("Outgoing", "Completed", "Zenvia"))
		self.assertEqual((log.get("from"), log.to, log.caller), ("4000", "+5548988887777", "Administrator"))

	def test_received_call_by_the_did_address(self):
		deal = make_deal("+55 48 98888-7777")
		body = chamada_fim(
			call_id=555,
			origem=leg("+5548988887777", "movel", "atendida", total=31),
			destino=leg("4000", "ramal", "atendida", falada=25, total=30, inicio="2019-09-06T11:18:20-03:00"),
		)

		self.post(body, tipo="did")

		log = frappe.get_doc("CRM Call Log", "zenvia-555")
		self.assertEqual((log.type, log.receiver), ("Incoming", "Administrator"))
		self.assertEqual((log.reference_doctype, log.reference_docname), ("CRM Deal", deal))

	def test_other_notifications_are_ignored(self):
		self.post({"id": 9, "tipo": "saldo", "valor": 10})
		self.assertFalse(frappe.db.exists("CRM Call Log", "zenvia-9"))


class TestZenviaSettings(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_token_is_checked_with_zenvia_on_save(self):
		refused = response(200, {"status": 401, "sucesso": False, "mensagem": "token invalido"})
		with (
			patch("crm.integrations.voip.zenvia.requests.request", return_value=refused) as call,
			self.assertRaises(frappe.ValidationError),
		):
			settings().save()
		self.assertEqual(call.call_args.args, ("get", "https://voice-api.zenvia.com/saldo"))

	def test_bad_caller_number_is_refused(self):
		doc = settings()
		doc.caller_number = "3000-0000"
		with (
			patch("crm.integrations.voip.zenvia.check_token"),
			self.assertRaises(frappe.ValidationError),
		):
			doc.save()

	def test_webhook_addresses_carry_the_secret_and_the_did_flag(self):
		doc = settings()
		with patch("crm.integrations.voip.zenvia.check_token"):
			doc.save()
		urls = doc.get_webhook_urls()
		self.assertTrue(urls["chamada_fim"].endswith(f"webhook.zenvia?key={SECRET}"))
		self.assertTrue(urls["did_fim"].endswith(f"key={SECRET}&tipo=did"))
