import { call } from 'frappe-ui'
import { reactive } from 'vue'
import { getRequest } from '../LeadSyncing/metaLeadsApi'

// HubTech API keys (credtech#175), served by the cred_hub app. Only admins
// see and manage them; the secret is shown once, when the key is created or
// rotated. Without the cred_hub app the page does not show up.
const API = 'cred_hub.api_keys.'

export const apiKeysApi = {
  // { keys: [{ name, label, prefix, secret_hint, status: Active | Revoked,
  //   scopes, pipelines, allowed_ips, expires_on, created_by, created_on,
  //   last_used_on, last_used_ip }], scopes: [{ value, label }], limit,
  //   legacy_until (YYYY-MM-DD) | null, legacy_users: [{ name, full_name }] }
  get: () => getRequest(API + 'get_api_keys'),
  // same as a key, plus `token` (shown once)
  create: (values) => call(API + 'create_api_key', values),
  update: (name, values) => call(API + 'update_api_key', { name, ...values }),
  rotate: (name) => call(API + 'rotate_api_key', { name }),
  revoke: (name) => call(API + 'revoke_api_key', { name }),
}

export const apiKeys = reactive({ enabled: false, loading: false, data: null })

export async function loadApiKeys() {
  apiKeys.loading = true
  try {
    apiKeys.data = await apiKeysApi.get()
    apiKeys.enabled = true
  } catch {
    apiKeys.data = null
    apiKeys.enabled = false
  } finally {
    apiKeys.loading = false
  }
}
