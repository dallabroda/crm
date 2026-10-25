import { describe, it, expect } from 'vitest'
import {
  applyStageRules,
  missingFieldsFromError,
  LOCKED_FIELDS,
} from '../../src/utils/pipelines'

const missing = [
  { fieldname: 'cpf', label: 'CPF', fieldtype: 'Data', options: '' },
]

describe('missingFieldsFromError', () => {
  it('ignores other errors', () => {
    expect(missingFieldsFromError(null)).toBe(null)
    expect(
      missingFieldsFromError({ exc_type: 'ValidationError', messages: ['x'] }),
    ).toBe(null)
  })

  it('reads an object message', () => {
    let error = {
      exc_type: 'MissingRequiredFieldsError',
      messages: [{ missing_fields: missing }],
    }
    expect(missingFieldsFromError(error)).toEqual(missing)
  })

  it('reads a JSON string message', () => {
    let error = {
      exc_type: 'MissingRequiredFieldsError',
      messages: [JSON.stringify({ missing_fields: missing })],
    }
    expect(missingFieldsFromError(error)).toEqual(missing)
  })

  it('reads raw _server_messages (list of JSON strings)', () => {
    let inner = JSON.stringify({
      message: JSON.stringify({ missing_fields: missing }),
    })
    let error = {
      exc_type: 'MissingRequiredFieldsError',
      _server_messages: JSON.stringify([inner]),
    }
    expect(missingFieldsFromError(error)).toEqual(missing)
  })

  it('returns null when the payload has no fields', () => {
    let error = {
      exc_type: 'MissingRequiredFieldsError',
      messages: ['not json', { missing_fields: [] }],
    }
    expect(missingFieldsFromError(error)).toBe(null)
  })
})

describe('applyStageRules', () => {
  const sections = [
    {
      name: 'details',
      columns: [
        {
          fields: [
            { fieldname: 'address', reqd: 0, read_only: 0 },
            { fieldname: 'cpf', reqd: 0, read_only: 0 },
            { fieldname: 'deal_value', reqd: 0, read_only: 0 },
            { fieldname: 'deal_owner', reqd: 0, read_only: 0 },
            'next_step',
          ],
        },
      ],
    },
    { name: 'contacts_section', contacts: [] },
  ]

  it('returns sections unchanged without rules', () => {
    expect(applyStageRules(sections, {})).toBe(sections)
    expect(applyStageRules(sections, null)).toBe(sections)
  })

  it('hides, requires and locks fields', () => {
    let out = applyStageRules(sections, {
      address: { visible: 0, required: 0, read_only: 0 },
      cpf: { visible: 1, required: 1, read_only: 0 },
      deal_value: { visible: 1, required: 0, read_only: 1 },
      next_step: { visible: 0, required: 0, read_only: 0 },
    })
    let fields = out[0].columns[0].fields
    expect(fields.map((f) => f.fieldname || f)).toEqual([
      'cpf',
      'deal_value',
      'deal_owner',
    ])
    expect(fields[0].reqd).toBe(1)
    expect(fields[1].read_only).toBe(1)
  })

  it('never hides or locks the funnel, stage and owner', () => {
    let rules = Object.fromEntries(
      LOCKED_FIELDS.map((f) => [f, { visible: 0, required: 0, read_only: 1 }]),
    )
    let out = applyStageRules(sections, rules)
    expect(out[0].columns[0].fields.find((f) => f.fieldname === 'deal_owner'))
      .toEqual({ fieldname: 'deal_owner', reqd: 0, read_only: 0 })
  })

  it('does not modify the input and keeps sections without columns', () => {
    let copy = JSON.parse(JSON.stringify(sections))
    let out = applyStageRules(sections, {
      cpf: { visible: 0, required: 0, read_only: 0 },
    })
    expect(sections).toEqual(copy)
    expect(out[1]).toBe(sections[1])
  })
})
