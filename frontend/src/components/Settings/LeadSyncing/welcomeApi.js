import { call } from 'frappe-ui'
import { reactive } from 'vue'
import { getRequest } from './metaLeadsApi'

// WhatsApp welcome message for new ad and form leads (credtech#53), served by
// the cred_hub app: the admin connects the company's Cred Chat once, then turns
// the message on per lead source with a template already approved by Meta.
const API = 'cred_hub.welcome.'

export const welcomeApi = {
  // { connected, account_id, account_name, error, inboxes: [{ id, name,
  //   phone, templates: [{ name, language, category, body, variables }] }] }
  getConnection: () => getRequest(API + 'get_chat_connection'),
  // the access key is checked on Cred Chat before it is kept, and never comes back
  connect: (accountId, accessToken) =>
    call(API + 'connect_chat', {
      account_id: accountId,
      access_token: accessToken,
    }),
  // also turns the welcome message off on every source
  disconnect: () => call(API + 'disconnect_chat'),
  // source: "facebook:<form id>" or the name of a Cred Hub Lead Source
  // { enabled, inbox_id, template_name, template_language,
  //   variables: [lead field per template variable], lead_fields: [{ fieldname, label }] }
  get: (source) => getRequest(API + 'get_welcome', { source }),
  save: (source, values) => call(API + 'save_welcome', { source, ...values }),
}

// One Cred Chat connection per company, shared by every source on the page
export const chat = reactive({
  connected: false,
  account_id: null,
  account_name: null,
  error: null,
  inboxes: [],
  loading: false,
})

export async function loadChat() {
  chat.loading = true
  try {
    Object.assign(chat, await welcomeApi.getConnection())
  } finally {
    chat.loading = false
  }
}
