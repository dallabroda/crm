import frappe

from crm.api.card_contacts import get_card_contacts
from crm.api.forms import get_form_schema
from crm.api.pipeline import get_pipeline_config, save_pipeline
from crm.fcrm.doctype.crm_pipeline import fields as field_catalog
from crm.tests import CRMTestCase as FrappeTestCase

ORG = "CRM Organization"


class TestCardContacts(FrappeTestCase):
	"""Dynamic forms phase 4 (credtech#195): a card's optional second organization, its name per funnel and
	whose contacts the card shows (owner decisions 1-3 of 28/10/2026)."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.pipeline = save_pipeline(
			{
				"pipeline_name": "Receivables test",
				"stages": [{"deal_status": "Collection"}],
				"second_organization_label": "Sacado",
				"default_contacts_from": "Both",
			}
		)
		self.assignor = self._organization("Cedente Test Org", "cedente@example.test")
		self.debtor = self._organization("Sacado Test Org", "sacado@example.test")
		self._contact("Ana", self.assignor, linked=True)
		self._contact("Beto", self.debtor, linked=False)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _organization(self, name, email):
		values = {"doctype": ORG, "organization_name": name}
		if frappe.get_meta(ORG).has_field("registry_email"):
			values["registry_email"] = email
		return frappe.get_doc(values).insert().name

	def _contact(self, first_name, organization, linked):
		doc = {
			"doctype": "Contact",
			"first_name": first_name,
			"company_name": None if linked else organization,
		}
		if linked:
			doc["links"] = [{"link_doctype": ORG, "link_name": organization}]
		return frappe.get_doc(doc).insert().name

	def _card(self, **values):
		return frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"pipeline": self.pipeline["name"],
				"status": self.pipeline["stages"][0]["name"],
				"organization": self.assignor,
				**values,
			}
		).insert(ignore_permissions=True)

	def _names(self, card):
		return [
			(o["role"], o["name"], [c["full_name"] for c in o["contacts"]])
			for o in get_card_contacts(card.name)["organizations"]
		]

	def test_funnel_names_the_second_organization(self):
		config = get_pipeline_config(self.pipeline["name"])
		self.assertEqual(
			(config["second_organization_label"], config["default_contacts_from"]), ("Sacado", "Both")
		)
		save_pipeline({"name": self.pipeline["name"], "fields": ["organization", "second_organization"]})
		schema = get_form_schema("CRM Deal", self.pipeline["name"])
		second = next(f for f in schema["fields"] if f["fieldname"] == "second_organization")
		self.assertEqual((schema["second_organization_label"], second["label"]), ("Sacado", "Sacado"))

	def test_second_organization_is_offered_but_not_added_to_funnels(self):
		self.assertIn("second_organization", field_catalog.catalog_fieldnames())
		self.assertNotIn("second_organization", field_catalog.default_pipeline_fields())

	def test_second_organization_must_be_another_one(self):
		with self.assertRaises(frappe.ValidationError):
			self._card(second_organization=self.assignor)

	def test_new_card_takes_the_funnel_default(self):
		self.assertEqual(self._card(second_organization=self.debtor).contacts_from, "Both")

	def test_contacts_follow_the_choice(self):
		card = self._card(second_organization=self.debtor)
		both = self._names(card)
		self.assertEqual(
			both,
			[("organization", self.assignor, ["Ana"]), ("second_organization", self.debtor, ["Beto"])],
		)
		card.db_set("contacts_from", "Second organization")
		self.assertEqual(self._names(card), [("second_organization", self.debtor, ["Beto"])])
		card.db_set("contacts_from", "Organization")
		self.assertEqual(self._names(card), [("organization", self.assignor, ["Ana"])])
		result = get_card_contacts(card.name)
		self.assertEqual(result["second_organization_label"], "Sacado")
		if frappe.get_meta(ORG).has_field("registry_email"):
			self.assertEqual(result["organizations"][0]["registry_email"], "cedente@example.test")

	def test_one_organization_shows_it_whatever_the_choice(self):
		card = self._card(contacts_from="Second organization")
		self.assertEqual(self._names(card), [("organization", self.assignor, ["Ana"])])

	def test_search_finds_the_card_by_its_second_organization(self):
		from crm.api.command_palette import search

		card = self._card(second_organization=self.debtor)
		matches = search("Sacado Test")["matches"]
		self.assertIn(card.name, [m["name"] for m in matches if m.get("doctype") == "CRM Deal"])
