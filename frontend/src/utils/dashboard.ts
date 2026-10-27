import { dayjs } from 'frappe-ui'
import { userLocale } from './locale'

export type DashboardDateRange = string | [string, string] | [] | null

export function getLastXDays(range: number = 30): string | null {
  const today = new Date()
  const lastXDate = new Date(today)
  lastXDate.setDate(today.getDate() - range)

  return `${dayjs(lastXDate).format('YYYY-MM-DD')},${dayjs(today).format(
    'YYYY-MM-DD',
  )}`
}

export function parseDateRange(range: DashboardDateRange): [string, string] {
  if (!range) return ['', '']
  const dates = Array.isArray(range) ? range : range.split(',')
  return [dates[0] || '', dates[1] || '']
}

export function formatter(range: DashboardDateRange) {
  const [from, to] = parseDateRange(range)
  return __('{0} to {1}', [formatRange(from), formatRange(to)])
}

export function formatRange(date: string) {
  const dateObj = new Date(date)
  return dateObj.toLocaleDateString(userLocale(), {
    month: 'short',
    day: 'numeric',
    year:
      dateObj.getFullYear() === new Date().getFullYear()
        ? undefined
        : 'numeric',
  })
}
