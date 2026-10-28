// Pure helpers of the API keys screen (credtech#175)

// Scopes as the screen groups them: one row per resource, read and write side by side
export const SCOPE_ROWS = [
  { label: 'Cards', read: 'cards_read', write: 'cards_write' },
  { label: 'Contacts', read: 'contacts_read', write: 'contacts_write' },
  {
    label: 'Organizations',
    read: 'organizations_read',
    write: 'organizations_write',
  },
  // CRM Lead: the incoming contact that becomes a card (the word "lead" is not shown, credtech#192)
  {
    label: 'Incoming contacts',
    read: null,
    write: 'leads_write',
    writeLabel: 'Create',
  },
  { label: 'Funnels', read: 'pipelines_read', write: null },
]
export const ADMIN_SCOPE = 'fields_admin'

// Cards (and the fields and rules of the funnels) only exist inside funnels
export function needsPipelines(scopes) {
  return ['cards_read', 'cards_write', ADMIN_SCOPE].some((s) =>
    scopes.includes(s),
  )
}

// "Cards: read / write, Contacts: read": one part per resource, words translated by `t`
export function scopeSummary(scopes, t = (text) => __(text)) {
  let parts = SCOPE_ROWS.map((row) => {
    let verbs = []
    if (row.read && scopes.includes(row.read)) verbs.push(t('read'))
    if (row.write && scopes.includes(row.write))
      verbs.push(t(row.writeLabel ? row.writeLabel.toLowerCase() : 'write'))
    return verbs.length ? `${t(row.label)}: ${verbs.join(' / ')}` : null
  }).filter(Boolean)
  if (scopes.includes(ADMIN_SCOPE))
    parts.push(t('Fields and rules of the stages (admin)'))
  return parts.join(', ')
}

// "28/10/2026" from the server's "2026-10-28[ 05:37:12]" (no timezone change: it is already the company's)
export function brDate(value) {
  if (!value) return ''
  let [year, month, day] = String(value).slice(0, 10).split('-')
  return `${day}/${month}/${year}`
}

// "28/10/2026 05:37"
export function brDateTime(value) {
  if (!value) return ''
  let time = String(value).slice(11, 16)
  return time ? `${brDate(value)} ${time}` : brDate(value)
}

// "DD/MM" for the warning about the old keys
export function dayMonth(isoDate) {
  if (!isoDate) return ''
  let [, month, day] = String(isoDate).slice(0, 10).split('-')
  return `${day}/${month}`
}

// The old keys keep working until legacy_until (inclusive)
export function legacyStopped(isoDate, today = new Date()) {
  if (!isoDate) return false
  let local = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return local > String(isoDate).slice(0, 10)
}

export function cleanIps(text) {
  return (text || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .join('\n')
}
