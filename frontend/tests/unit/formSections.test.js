import { describe, it, expect } from 'vitest'
import { funnelSection, withoutFields } from '../../src/utils/pipelines'

// Schema fields as crm.api.forms.get_form_schema sends them (funnel order)
const schema = [
  { fieldname: 'pipeline', visible: 1, locked: 1 },
  { fieldname: 'ch_renda', visible: 1, locked: 0, reqd: 1 },
  { fieldname: 'next_step', visible: 0, locked: 0 },
  { fieldname: 'deal_value', visible: 1, locked: 0 },
]

describe('funnelSection', () => {
  it('keeps the visible, unlocked fields in the funnel order', () => {
    let section = funnelSection(schema, 'Card fields')
    expect(section.label).toBe('Card fields')
    expect(section.columns[0].fields.map((f) => f.fieldname)).toEqual([
      'ch_renda',
      'deal_value',
    ])
  })

  it('is empty when nothing is visible', () => {
    expect(funnelSection([{ fieldname: 'x', visible: 0 }], 'L')).toBe(null)
    expect(funnelSection(null, 'L')).toBe(null)
  })
})

describe('withoutFields', () => {
  const sections = [
    {
      name: 'details',
      columns: [
        {
          fields: [
            { fieldname: 'deal_value' },
            'next_step',
            { fieldname: 'company_description' },
          ],
        },
      ],
    },
    { name: 'only_funnel', columns: [{ fields: [{ fieldname: 'ch_renda' }] }] },
    { name: 'contacts_section' },
  ]

  it('takes the funnel fields out of the layout and drops emptied sections', () => {
    let out = withoutFields(sections, ['deal_value', 'next_step', 'ch_renda'])
    expect(out.map((s) => s.name)).toEqual(['details', 'contacts_section'])
    expect(out[0].columns[0].fields).toEqual([
      { fieldname: 'company_description' },
    ])
  })

  it('leaves the layout alone without names', () => {
    expect(withoutFields(sections, [])).toBe(sections)
  })
})
