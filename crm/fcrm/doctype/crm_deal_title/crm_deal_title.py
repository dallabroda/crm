# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

from frappe.model.document import Document

class CRMDealTitle(Document):
	def validate(self):
		# Espécies que exigem anexo obrigatório na CENPROT
		attachment_species = {"CCB", "CH", "NP", "CD", "CPS", "CA", "CL", "CM", "TA"}
		self.requires_attachment = 1 if self.species in attachment_species else 0
		if not self.updated_amount:
			self.updated_amount = self.original_amount
