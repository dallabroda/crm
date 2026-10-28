import { describe, it, expect } from 'vitest'
import {
  globalFormSections,
  layoutFieldnames,
  requiredOutsideLayout,
} from '../../src/utils/pipelines'

const labels = { form: 'Organization fields', created: 'Created fields' }
const layout = [
  {
    name: 'details',
    columns: [{ fields: [{ fieldname: 'website' }, 'industry'] }],
  },
  { name: 'address_section', columns: [{ fields: [{ fieldname: 'notes' }] }] },
]
const schemaFields = [
  { fieldname: 'organization_name', visible: 1, locked: 1 },
  { fieldname: 'cnpj', visible: 1, locked: 0, required: 1 },
  { fieldname: 'website', visible: 1, locked: 0 },
  { fieldname: 'industry', visible: 0, locked: 0 },
  { fieldname: 'ch_tier', visible: 1, locked: 0, is_created: 1 },
]

describe('globalFormSections', () => {
  it('keeps the layout and adds created fields until the form is saved', () => {
    let out = globalFormSections(
      layout,
      { configured: false, fields: schemaFields },
      labels,
    )
    expect(out.map((s) => s.name)).toEqual([
      'details',
      'address_section',
      'created_fields',
    ])
    expect(out[2].columns[0].fields.map((f) => f.fieldname)).toEqual([
      'ch_tier',
    ])
    expect(out[2].notInLayout).toBe(true)
  })

  it('follows the saved form and keeps only what is not a form field', () => {
    let out = globalFormSections(
      layout,
      { configured: true, fields: schemaFields },
      labels,
    )
    expect(out.map((s) => s.name)).toEqual(['form_fields', 'address_section'])
    expect(out[0].label).toBe('Organization fields')
    expect(out[0].columns[0].fields.map((f) => f.fieldname)).toEqual([
      'cnpj',
      'website',
      'ch_tier',
    ])
  })

  it('leaves the layout alone without a schema', () => {
    expect(globalFormSections(layout, null, labels)).toBe(layout)
  })
})

describe('requiredOutsideLayout', () => {
  it('asks only the required fields the quick entry does not have', () => {
    let tabs = [
      { sections: [{ columns: [{ fields: [{ fieldname: 'website' }] }] }] },
    ]
    expect(layoutFieldnames(tabs)).toEqual(new Set(['website']))
    let fields = [
      ...schemaFields,
      { fieldname: 'website', required: 1, locked: 0 },
      {
        fieldname: 'size',
        required: 1,
        locked: 0,
        fieldtype: 'Select',
        options: [
          { label: 'S', value: 'S' },
          { label: 'L', value: 'L' },
        ],
      },
    ]
    let out = requiredOutsideLayout(fields, tabs)
    expect(out.map((f) => f.fieldname)).toEqual(['cnpj', 'size'])
    expect(out[1].options).toBe('S\nL')
  })
})
