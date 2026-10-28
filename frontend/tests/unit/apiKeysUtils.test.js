import { describe, expect, it } from 'vitest'
import {
  brDate,
  brDateTime,
  cleanIps,
  dayMonth,
  legacyStopped,
  needsPipelines,
  scopeSummary,
} from '@/components/Settings/ApiKeys/apiKeysUtils'

describe('API keys screen helpers', () => {
  it('shows the end of the old keys as DD/MM', () => {
    expect(dayMonth('2026-11-27')).toBe('27/11')
    expect(dayMonth(null)).toBe('')
  })

  it('old keys still work on the last day and stop the day after', () => {
    expect(legacyStopped('2026-11-27', new Date(2026, 10, 27, 23, 59))).toBe(
      false,
    )
    expect(legacyStopped('2026-11-27', new Date(2026, 10, 28, 0, 1))).toBe(true)
    expect(legacyStopped(null)).toBe(false)
  })

  it('asks for funnels only when the key reaches cards or their fields', () => {
    expect(needsPipelines(['contacts_read'])).toBe(false)
    expect(needsPipelines(['cards_read'])).toBe(true)
    expect(needsPipelines(['fields_admin'])).toBe(true)
  })

  it('keeps one IP per line, without blanks', () => {
    expect(cleanIps(' 203.0.113.10 \n\n203.0.113.0/24\n')).toBe(
      '203.0.113.10\n203.0.113.0/24',
    )
  })

  it('summarizes permissions per resource, in the user words', () => {
    const PT = {
      Cards: 'Cards',
      Contacts: 'Contatos',
      Funnels: 'Funis',
      read: 'ler',
      write: 'escrever',
      'Fields and rules of the stages (admin)':
        'Campos e regras das etapas (admin)',
    }
    const t = (text) => PT[text] || text
    expect(
      scopeSummary(
        ['cards_read', 'cards_write', 'contacts_read', 'pipelines_read'],
        t,
      ),
    ).toBe('Cards: ler / escrever, Contatos: ler, Funis: ler')
    expect(scopeSummary(['leads_write'], t)).toBe('Incoming contacts: create')
    expect(scopeSummary(['fields_admin'], t)).toBe(
      'Campos e regras das etapas (admin)',
    )
  })

  it('shows dates as DD/MM/YYYY without moving the day', () => {
    expect(brDate('2026-10-28')).toBe('28/10/2026')
    expect(brDate('2026-10-28 23:59:59.123')).toBe('28/10/2026')
    expect(brDateTime('2026-10-28 05:37:12.5')).toBe('28/10/2026 05:37')
    expect(brDateTime('2026-11-27')).toBe('27/11/2026')
    expect(brDate(null)).toBe('')
  })
})
