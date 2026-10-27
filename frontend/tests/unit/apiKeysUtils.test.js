import { describe, expect, it } from 'vitest'
import {
  cleanIps,
  dayMonth,
  legacyStopped,
  needsPipelines,
} from '@/components/Settings/ApiKeys/apiKeysUtils'

describe('API keys screen helpers', () => {
  it('shows the end of the old keys as DD/MM', () => {
    expect(dayMonth('2026-11-27')).toBe('27/11')
    expect(dayMonth(null)).toBe('')
  })

  it('old keys still work on the last day and stop the day after', () => {
    expect(legacyStopped('2026-11-27', new Date(2026, 10, 27, 23, 59))).toBe(false)
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
})
