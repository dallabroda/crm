# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


def balance_of(title) -> float:
	"""What is still owed on a title (credtech#315). `updated_amount` is the open balance: it starts as the original
	amount, the analyst may correct it (interest, discount) and every payment lowers it. A paid title has 0 left, so
	"updated or original" would bring the original value back: a title with payments keeps its balance as it is."""
	updated = flt(title.get("updated_amount"))
	if updated or flt(title.get("paid_amount")):
		return updated
	return flt(title.get("original_amount"))


class CRMDealTitle(Document):
	def validate(self):
		# Espécies que exigem anexo obrigatório na CENPROT
		attachment_species = {"CCB", "CH", "NP", "CD", "CPS", "CA", "CL", "CM", "TA", "CT", "DM", "DS"}
		self.requires_attachment = 1 if (self.species or "").upper() in attachment_species else 0
		if not self.updated_amount and not flt(self.paid_amount):
			self.updated_amount = self.original_amount
