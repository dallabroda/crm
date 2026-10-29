<template>
  <Dialog
    v-model:open="show"
    :title="__('Request another telephony integration')"
    :size="'xl'"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'Tell us which telephony company you use. CredTech studies the integration from the API documentation and gets back to you.',
            )
          }}
        </p>
        <FormControl
          v-model="provider"
          :label="__('Telephony company')"
          :placeholder="__('E.g. Vonage')"
          :maxlength="140"
          required
        />
        <FormControl
          v-model="docsUrl"
          :label="__('API documentation link (optional)')"
          placeholder="https://"
          :maxlength="500"
        />
        <FormControl
          v-model="usage"
          type="textarea"
          :label="__('How do you use it? (optional)')"
          :placeholder="
            __('E.g. click to call from the deal and keep the recording')
          "
          :maxlength="2000"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="show = false"
          />
          <Button
            variant="solid"
            :label="__('Send request')"
            :loading="sending"
            :disabled="!provider.trim()"
            @click="send"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
// Asks CredTech for an integration with another telephony company (credtech#259): the request becomes a card in
// CredTech's HubTech and an e-mail to contato@ (cred_hub.telephony_request)
import { Dialog, FormControl, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, watch } from 'vue'

const show = defineModel({ type: Boolean })

const provider = ref('')
const docsUrl = ref('')
const usage = ref('')
const sending = ref(false)
const error = ref('')

watch(show, (open) => {
  if (!open) return
  provider.value = ''
  docsUrl.value = ''
  usage.value = ''
  error.value = ''
})

async function send() {
  sending.value = true
  error.value = ''
  try {
    await call('cred_hub.telephony_request.request_integration', {
      provider: provider.value,
      docs_url: docsUrl.value,
      usage: usage.value,
    })
    toast.success(__('Request sent. The CredTech team will get back to you.'))
    show.value = false
  } catch (err) {
    error.value =
      err?.messages?.[0] || err?.message || __('Something went wrong')
  } finally {
    sending.value = false
  }
}
</script>
