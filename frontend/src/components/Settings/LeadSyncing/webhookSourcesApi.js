import { call } from 'frappe-ui'

// Lead sources that post to Cred Hub (credtech#51): Google Ads lead forms,
// the company's website, Typeform and any other tool (Zapier, Make...).
// Every source has its own URL and key and sends its leads to one funnel.
const API = 'cred_hub.lead_intake.'

export const webhookSourcesApi = {
  // [{ name, type, label, pipeline, enabled, url, key_hint, last_lead_at }]
  list: () => call(API + 'get_webhook_sources'),
  // { name, url, key }: the key is shown this once
  create: (type, label, pipeline) =>
    call(API + 'create_webhook_source', { type, label, pipeline }),
  // any of label / pipeline / enabled
  update: (name, values) =>
    call(API + 'update_webhook_source', { name, ...values }),
  // { key }
  regenerateKey: (name) => call(API + 'regenerate_webhook_key', { name }),
  remove: (name) => call(API + 'delete_webhook_source', { name }),
}

// icon: whole class names, so the icon CSS is generated for them
export const SOURCE_TYPES = [
  {
    value: 'google_ads',
    label: __('Google Ads lead form'),
    icon: 'lucide-megaphone',
  },
  { value: 'website', label: __('Website form'), icon: 'lucide-globe' },
  { value: 'typeform', label: __('Typeform'), icon: 'lucide-clipboard-list' },
  {
    value: 'webhook',
    label: __('Other tools (Zapier, Make, API)'),
    icon: 'lucide-webhook',
  },
]

export function sourceType(value) {
  return SOURCE_TYPES.find((t) => t.value === value) || SOURCE_TYPES[3]
}
