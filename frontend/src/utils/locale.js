import { dayjs } from 'frappe-ui'
import 'dayjs/esm/locale/pt-br'

// dayjs locales bundled with the app, keyed by base language
const DAYJS_LOCALES = { pt: 'pt-br' }

// The signed-in user's language (boot "lang", e.g. "pt-BR"), as a tag Intl accepts
export function userLocale() {
  const lang = (window.lang || 'en').replace('_', '-')
  try {
    return Intl.getCanonicalLocales(lang)[0]
  } catch {
    return 'en'
  }
}

// Whether the user's language reads time on a 24-hour clock ("15:30" rather than "3:30 PM")
export function uses24HourClock(locale = userLocale()) {
  const { hourCycle } = new Intl.DateTimeFormat(locale, {
    hour: 'numeric',
  }).resolvedOptions()
  return hourCycle === 'h23' || hourCycle === 'h24'
}

/**
 * Adapts an English dayjs format to the user's language: the 12-hour clock
 * becomes "HH:mm" and the month moves after the day ("MMM D" -> "D MMM") where
 * the language reads it that way. English formats are returned unchanged.
 */
export function localizeFormat(format, locale = userLocale()) {
  if (!format || locale.startsWith('en')) return format
  let out = format
  if (uses24HourClock(locale)) out = out.replace(/h{1,2}:mm\s?a/g, 'HH:mm')
  return out.replace(/MMM D, YYYY/g, 'D MMM YYYY').replace(/MMM D\b/g, 'D MMM')
}

// Applies the user's language to dates (dayjs) and to numbers in charts, which read <html lang>
export function applyUserLocale() {
  const locale = userLocale()
  document.documentElement.lang = locale
  const dayjsLocale = DAYJS_LOCALES[locale.split('-')[0]]
  dayjs.locale(dayjsLocale || 'en')
}
