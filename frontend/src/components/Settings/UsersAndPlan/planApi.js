import { call } from 'frappe-ui'
import { reactive } from 'vue'
import { getRequest } from '../LeadSyncing/metaLeadsApi'

// Users and Plan (credtech#25), served by the cred_hub app: 2 free users per
// company, extra users paid monthly by card on Asaas. The card is typed on the
// Asaas invoice page, never here. Off while `credhub_billing` is off: the page
// does not show up.
const API = 'cred_hub.billing.'

export const planApi = {
  // { enabled, limit, free, extras, pending_extras, scheduled_extras,
  //   scheduled_from, upgrade: { extras, paid_extras, due_date, overdue,
  //   invoice_url } | null, grace_until, used_active, used_invited, status:
  //   Free | Awaiting Payment | Active | Past Due | Canceled, next_due, amount,
  //   price_per_user, currency, invoice_url, paused_users: [{ name,
  //   full_name }], unlimited, needs_payer, payer: { name, email } | null }
  get: () => getRequest(API + 'get_plan'),
  // { ok, invoice_url, status, amount, scheduled_from } or
  // { ok: false, field, message }
  // payer (first time only): { name, tax_id, email, phone, postal_code }
  requestExtraUsers: (quantity, payer) =>
    call(API + 'request_extra_users', { quantity, payer }),
}

export const plan = reactive({ enabled: false, loading: false, data: null })

// Only admins see the plan; without the cred_hub app or with billing off the
// page stays hidden
export async function loadPlan() {
  plan.loading = true
  try {
    const data = await planApi.get()
    plan.data = data?.enabled ? data : null
    plan.enabled = Boolean(data?.enabled)
  } catch {
    plan.data = null
    plan.enabled = false
  } finally {
    plan.loading = false
  }
}

export function openInvoice(url) {
  window.open(url, '_blank', 'noopener')
}

// Plan status (English in the backend) as the admin reads it
export function statusBadge(status) {
  return (
    {
      Free: { label: __('Free plan'), theme: 'gray' },
      'Awaiting Payment': { label: __('Awaiting payment'), theme: 'orange' },
      Active: { label: __('Active'), theme: 'green' },
      'Past Due': { label: __('Payment overdue'), theme: 'red' },
      Canceled: { label: __('Canceled'), theme: 'gray' },
    }[status] || { label: status, theme: 'gray' }
  )
}

// Past Due still within the grace days (dates come as YYYY-MM-DD, local)
export function inGrace(data, today = localToday()) {
  return Boolean(data?.grace_until && data.grace_until >= today)
}

function localToday() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function usage(data) {
  const used = (data?.used_active || 0) + (data?.used_invited || 0)
  const limit = data?.limit || 0
  return { used, limit, full: !data?.unlimited && used >= limit }
}

// What saving `quantity` extra users does, so the page can say it before the
// admin confirms. Mirrors cred_hub.billing.request_extra_users.
export function describeChange(data, quantity) {
  quantity = Math.max(0, parseInt(quantity, 10) || 0)
  const monthly = (data?.price_per_user || 0) * quantity
  if (quantity === chosenExtras(data)) return { kind: 'same', monthly }
  if (data?.status !== 'Active') {
    return { kind: quantity ? 'subscribe' : 'free', monthly }
  }
  // with an upgrade still unpaid, what is already paid is the base
  const paid = data.upgrade ? data.upgrade.paid_extras : data.extras
  if (quantity > paid) return { kind: 'increase', monthly }
  if (quantity < paid)
    return { kind: quantity ? 'decrease' : 'cancel', monthly }
  // back to what is paid: drops a scheduled decrease or an unpaid upgrade
  return { kind: 'keep', monthly }
}

// Extra users the company asked for, counting a decrease scheduled for the
// next due date, an upgrade still unpaid and a first subscription not paid yet
export function chosenExtras(data) {
  if (!data) return 0
  if (data.status === 'Active') {
    return data.scheduled_extras ?? data.upgrade?.extras ?? data.extras ?? 0
  }
  if (data.status === 'Awaiting Payment') return data.pending_extras || 0
  // Free and Canceled have no paid seats, whatever was contracted before
  return data.status === 'Past Due' ? data.extras || 0 : 0
}

// Users that take a seat beyond the new limit, so a decrease can warn who is
// paused at the turn (most recent first)
export function overLimitAfter(data, quantity) {
  const limit = (data?.free || 0) + Math.max(0, parseInt(quantity, 10) || 0)
  return Math.max(0, usage(data).used - limit)
}
