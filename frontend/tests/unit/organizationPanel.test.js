import { expect, it } from 'vitest'
import { organizationPanelSections } from '@/utils/organizationPanel'

const f = (fieldname) => ({ fieldname, label: fieldname })
const names = (section) => section.fields.map((x) => x.fieldname)

it('splits the panel into Detalhes and Dados da Receita, in the Figma order', () => {
  const sections = organizationPanelSections(
    [
      f('cnpj'),
      f('city'),
      f('situacao_extra'),
      f('registry_phone'),
      f('website'),
      f('organization_name'),
      f('custom_field'),
      f('registration_status'),
    ],
    ['cnpj', 'situacao_extra'],
  )
  expect(sections.map((s) => s.label)).toEqual([
    'Detalhes',
    'Dados da Receita (CNPJ)',
  ])
  expect(names(sections[0])).toEqual([
    'organization_name',
    'website',
    'city',
    'custom_field',
  ])
  expect(names(sections[1])).toEqual([
    'cnpj',
    'registration_status',
    'registry_phone',
    'situacao_extra',
  ])
})

it('leaves out a section without fields', () => {
  const sections = organizationPanelSections([f('website')])
  expect(sections.map((s) => s.name)).toEqual(['details'])
})
