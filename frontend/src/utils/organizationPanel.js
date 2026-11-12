// The Organization side panel (Figma 807:2): "Detalhes" with the company's
// own fields, then "Dados da Receita (CNPJ)" with what the Receita Federal
// lookup fills in. Each section keeps the Figma order; fields it doesn't
// list follow in the order they came.

// the Receita lookup's fields, also when the cred_hub section isn't set up
export const RECEITA_FIELDS = [
  'cnpj',
  'registration_status',
  'main_cnae',
  'legal_nature',
  'company_size',
  'is_mei',
  'activity_start_date',
  'years_in_business',
  'share_capital',
  'registry_phone',
  'registry_email',
]

const DETAILS_ORDER = [
  'organization_name',
  'company_description',
  'description',
  'website',
  'industry',
  'no_of_employees',
  'address',
  'state',
  'city',
  'neighborhood',
  'annual_revenue',
  'linkedin',
]

function inOrder(fields, order) {
  const rank = (f) => {
    const i = order.indexOf(f.fieldname)
    return i === -1 ? order.length : i
  }
  // a stable sort keeps the unlisted fields in the order they came
  return [...fields].sort((a, b) => rank(a) - rank(b))
}

// fields: every field of the panel; receitaSection: fieldnames of the
// cred_hub "Dados da Receita (CNPJ)" section, when the site has it
export function organizationPanelSections(fields, receitaSection = []) {
  const receita = new Set([...RECEITA_FIELDS, ...receitaSection])
  const receitaOrder = [...RECEITA_FIELDS, ...receitaSection]
  const details = fields.filter((f) => !receita.has(f.fieldname))
  const registry = fields.filter((f) => receita.has(f.fieldname))
  return [
    {
      name: 'details',
      label: __('Detalhes'),
      fields: inOrder(details, DETAILS_ORDER),
    },
    {
      name: 'registry',
      label: __('Dados da Receita (CNPJ)'),
      fields: inOrder(registry, receitaOrder),
    },
  ].filter((section) => section.fields.length)
}
