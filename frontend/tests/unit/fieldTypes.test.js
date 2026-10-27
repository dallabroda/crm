import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  fieldTypeLabel,
  fieldTypeOptions,
} from '@/components/Settings/Fields/fieldTypes'

// The pt-BR strings of crm/locale/pt_BR.po for the field catalog
const PT_BR = {
  'Linked record': 'Vínculo',
  Contact: 'Contato',
  Organization: 'Organização',
  Pipeline: 'Funil',
  Status: 'Situação',
  User: 'Usuário',
  Source: 'Origem',
  Industry: 'Setor de Atuação',
  Text: 'Texto',
  'Amount (R$)': 'Valor (R$)',
  'List of options': 'Lista de opções',
  'Yes/No': 'Sim/Não',
  'Date and time': 'Data e hora',
  'Long text': 'Texto longo',
  Percentage: 'Porcentagem',
  'Link to contact or organization': 'Vínculo com contato ou organização',
}

describe('field type labels', () => {
  let original
  beforeEach(() => {
    original = globalThis.__
    globalThis.__ = (msg) => PT_BR[msg] || msg
  })
  afterEach(() => {
    globalThis.__ = original
  })

  it.each([
    ['CRM Pipeline', 'Vínculo: Funil'],
    ['CRM Deal Status', 'Vínculo: Situação'],
    ['User', 'Vínculo: Usuário'],
    ['CRM Organization', 'Vínculo: Organização'],
    ['CRM Lead Source', 'Vínculo: Origem'],
    ['CRM Industry', 'Vínculo: Setor de Atuação'],
    ['Contact', 'Vínculo: Contato'],
  ])('shows a link to %s as "%s", never "Ligação"', (options, label) => {
    expect(fieldTypeLabel({ fieldtype: 'Link', options })).toBe(label)
  })

  it('never shows the internal doctype name of an unknown target untranslated by us', () => {
    // Unknown targets go through the translation, like any doctype name
    globalThis.__ = (msg) =>
      ({ ...PT_BR, 'CRM Territory X': 'Território X' })[msg] || msg
    expect(
      fieldTypeLabel({ fieldtype: 'Link', options: 'CRM Territory X' }),
    ).toBe('Vínculo: Território X')
    expect(fieldTypeLabel({ fieldtype: 'Link' })).toBe('Vínculo')
  })

  it.each([
    ['Data', 'Texto'],
    ['Currency', 'Valor (R$)'],
    ['Select', 'Lista de opções'],
    ['Check', 'Sim/Não'],
    ['Datetime', 'Data e hora'],
    ['Small Text', 'Texto longo'],
    ['Percent', 'Porcentagem'],
  ])('labels %s as "%s"', (fieldtype, label) => {
    expect(fieldTypeLabel({ fieldtype })).toBe(label)
  })

  it('offers the link type in "New field" as a link to contact or organization', () => {
    const link = fieldTypeOptions().find((o) => o.value === 'Link')
    expect(link.label).toBe('Vínculo com contato ou organização')
  })

  it('translates at call time, so a language change is followed', () => {
    expect(fieldTypeLabel({ fieldtype: 'Link', options: 'CRM Pipeline' })).toBe(
      'Vínculo: Funil',
    )
    globalThis.__ = (msg) => msg
    expect(fieldTypeLabel({ fieldtype: 'Link', options: 'CRM Pipeline' })).toBe(
      'Linked record: Pipeline',
    )
  })
})
