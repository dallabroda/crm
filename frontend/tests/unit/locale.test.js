import { afterEach, describe, expect, it, vi } from 'vitest'

const dayjsLocale = vi.fn()
vi.mock('frappe-ui', () => ({ dayjs: { locale: dayjsLocale } }))
vi.mock('dayjs/esm/locale/pt-br', () => ({}))

const { applyUserLocale, localizeFormat, userLocale, uses24HourClock } =
  await import('@/utils/locale')

describe('user locale', () => {
  afterEach(() => {
    delete window.lang
    dayjsLocale.mockClear()
  })

  it('reads the boot language as an Intl tag', () => {
    window.lang = 'pt-BR'
    expect(userLocale()).toBe('pt-BR')
    window.lang = 'pt_BR'
    expect(userLocale()).toBe('pt-BR')
  })

  it('falls back to English without a language or with a broken one', () => {
    expect(userLocale()).toBe('en')
    window.lang = 'not a language!'
    expect(userLocale()).toBe('en')
  })

  it('knows which languages read a 24-hour clock', () => {
    expect(uses24HourClock('pt-BR')).toBe(true)
    expect(uses24HourClock('en-US')).toBe(false)
  })

  it('applies the language to <html lang> and to dayjs', () => {
    window.lang = 'pt-BR'
    applyUserLocale()
    expect(document.documentElement.lang).toBe('pt-BR')
    expect(dayjsLocale).toHaveBeenCalledWith('pt-br')

    window.lang = 'en'
    applyUserLocale()
    expect(dayjsLocale).toHaveBeenLastCalledWith('en')
  })
})

describe('localizeFormat', () => {
  it('keeps English formats as they are', () => {
    expect(localizeFormat('D MMM, hh:mm a', 'en')).toBe('D MMM, hh:mm a')
    expect(localizeFormat('ddd, MMM D, YYYY | hh:mm a', 'en-US')).toBe(
      'ddd, MMM D, YYYY | hh:mm a',
    )
  })

  it('uses the 24-hour clock and puts the day before the month in Portuguese', () => {
    expect(localizeFormat('D MMM, hh:mm a', 'pt-BR')).toBe('D MMM, HH:mm')
    expect(localizeFormat('ddd, MMM D, YYYY | hh:mm a', 'pt-BR')).toBe(
      'ddd, D MMM YYYY | HH:mm',
    )
    expect(localizeFormat('ddd, MMM D, YYYY h:mm a', 'pt-BR')).toBe(
      'ddd, D MMM YYYY HH:mm',
    )
    expect(localizeFormat('MMM D, dddd', 'pt-BR')).toBe('D MMM, dddd')
    expect(localizeFormat('hh:mm a', 'pt-BR')).toBe('HH:mm')
  })

  it('leaves formats without a month or a 12-hour clock alone', () => {
    expect(localizeFormat('DD/MM/YYYY HH:mm:ss', 'pt-BR')).toBe(
      'DD/MM/YYYY HH:mm:ss',
    )
    expect(localizeFormat('', 'pt-BR')).toBe('')
  })
})
