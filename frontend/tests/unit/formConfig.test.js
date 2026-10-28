import { describe, it, expect } from 'vitest'
import {
  configPayload,
  configRows,
  equalizedRows,
  newRow,
  setFlag,
  unusedFields,
} from '../../src/utils/formConfig'

// as crm.api.forms.get_form_schema sends them for "all stages"
const schema = [
  {
    fieldname: 'status',
    label: 'Stage',
    locked: 1,
    visible: 1,
    required: 1,
    read_only: 0,
    read_only_rule: 0,
  },
  {
    fieldname: 'deal_value',
    label: 'Value',
    locked: 0,
    visible: 1,
    required: 0,
    read_only: 0,
    read_only_rule: 0,
  },
  {
    fieldname: 'next_step',
    label: 'Next step',
    locked: 0,
    visible: null,
    required: 0,
    // read only by itself, not by the funnel
    read_only: 1,
    read_only_rule: 0,
  },
]

describe('configRows', () => {
  it('keeps the funnel rule, not the rendered read only', () => {
    let rows = configRows(schema)
    expect(rows[2].read_only).toBe(0)
    expect(rows[2].visible).toBe(null)
    expect(rows[0].locked).toBe(true)
  })
})

describe('setFlag', () => {
  it('makes a required or read only field visible', () => {
    let [, , row] = configRows(schema)
    setFlag(row, 'required', true)
    expect([row.visible, row.required]).toEqual([1, 1])
  })

  it('clears required and read only when hiding', () => {
    let [, row] = configRows(schema)
    setFlag(row, 'read_only', true)
    setFlag(row, 'visible', false)
    expect([row.visible, row.required, row.read_only]).toEqual([0, 0, 0])
  })

  it('does not touch locked fields', () => {
    let [row] = configRows(schema)
    setFlag(row, 'visible', false)
    expect(row.visible).toBe(1)
  })
})

describe('configPayload', () => {
  it('sends the unlocked rows in order, with null for what varies', () => {
    expect(configPayload(configRows(schema))).toEqual([
      { fieldname: 'deal_value', visible: 1, required: 0, read_only: 0 },
      { fieldname: 'next_step', visible: null, required: 0, read_only: 0 },
    ])
  })
})

describe('equalizedRows', () => {
  it('lists the rows that varied by stage and were changed', () => {
    let rows = configRows(schema)
    expect(equalizedRows(rows)).toEqual([])
    setFlag(rows[2], 'visible', true)
    expect(equalizedRows(rows).map((r) => r.fieldname)).toEqual(['next_step'])
  })
})

describe('unusedFields and newRow', () => {
  const catalog = [
    { fieldname: 'status', locked: 1 },
    { fieldname: 'deal_value' },
    { fieldname: 'ch_old', disabled: 1 },
    { fieldname: 'ch_cpf', label: 'CPF', fieldtype: 'Data', is_standard: 0 },
  ]

  it('offers only the fields the funnel does not use', () => {
    let free = unusedFields(catalog, configRows(schema))
    expect(free.map((f) => f.fieldname)).toEqual(['ch_cpf'])
  })

  it('starts a new field visible and optional', () => {
    let row = newRow(catalog[3])
    expect([row.visible, row.required, row.read_only]).toEqual([1, 0, 0])
    expect(row.is_created).toBe(true)
    expect(equalizedRows([row])).toEqual([])
  })
})
