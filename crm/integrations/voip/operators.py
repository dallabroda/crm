"""The telephony operators the CRM integrates with (credtech#268). A new operator is an adapter
(see base.Operator) added to OPERATORS and a webhook route in webhook.py when it has one."""

from crm.integrations.voip.api4com import API4Com
from crm.integrations.voip.base import Operator
from crm.integrations.voip.nvoip import Nvoip
from crm.integrations.voip.telnyx import Telnyx
from crm.integrations.voip.wavix import Wavix

OPERATORS: dict[str, Operator] = {
	operator.key: operator for operator in (API4Com(), Nvoip(), Wavix(), Telnyx())
}


def get_operator(key: str) -> Operator:
	return OPERATORS[key]


def get_operator_by_medium(medium: str | None) -> Operator | None:
	return next((operator for operator in OPERATORS.values() if operator.medium == medium), None)
