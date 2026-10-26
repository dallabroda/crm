import { call, frappeRequest } from 'frappe-ui'

// Meta Lead Ads connection, served by the cred_hub app (credtech#51): the
// company admin connects Facebook once, picks the funnel of each lead form and
// leads arrive by webhook within seconds.
const API = 'cred_hub.meta_leads.'

// Reads are whitelisted for GET only; `call` always POSTs
export function getRequest(method, params = {}) {
  return frappeRequest({ url: method, method: 'GET', params })
}

export const metaLeadsApi = {
  // { auth_url }: Facebook login in a popup; the popup closes itself when done
  startConnect: () => call(API + 'start_facebook_connect'),
  // { connected, user_name, error, pages: [{ id, name, forms: [{ id, name,
  //   pipeline, enabled, last_lead_at, questions: [{ key, label, mapped_to }] }] }] }
  getConnection: () => getRequest(API + 'get_facebook_connection'),
  // any of pipeline / enabled / mapping ({ question key: CRM Lead field })
  saveForm: (formId, values) =>
    call(API + 'save_facebook_form', { form_id: formId, ...values }),
  disconnect: () => call(API + 'disconnect_facebook'),
  // [{ time, status: Created | Duplicate | Failed, lead, lead_name, form_name
  //    (Meta) or source_label (other sources),
  //    pipeline, assigned_to, error, card: { doctype, name },
  //    welcome: Queued | Sent | Failed | null, welcome_error, welcome_url }]
  // every source when `source` is left out
  getActivity: (source) =>
    getRequest(API + 'get_lead_source_activity', source ? { source } : {}),
}
