<template>
  <Dialog v-model:open="open" :title="__('Send WhatsApp')">
    <template #default>
      <div class="flex flex-col gap-4" data-testid="smartchat-whatsapp">
        <div class="text-p-base text-ink-gray-7">
          {{ [name, options.data?.phone || phone].filter(Boolean).join(' · ') }}
        </div>

        <div v-if="options.loading" class="text-p-base text-ink-gray-5">
          {{ __('Loading SmartChat inboxes...') }}
        </div>
        <p
          v-else-if="options.data && !options.data.connected"
          class="text-p-base text-ink-gray-7"
        >
          {{
            __(
              "Connect the company's SmartChat first (Settings › Integrations › Lead Sources).",
            )
          }}
        </p>
        <ErrorMessage
          v-else-if="options.data?.error || options.error"
          :message="options.data?.error || options.error"
        />
        <p
          v-else-if="options.data && !inboxes.length"
          class="text-p-base text-ink-gray-7"
        >
          {{ __('You are not a member of any WhatsApp inbox in SmartChat.') }}
        </p>

        <template v-else-if="sent">
          <p class="text-p-base text-ink-gray-8">
            {{ __('Message sent through SmartChat.') }}
          </p>
        </template>

        <template v-else-if="inboxes.length">
          <FormControl
            type="select"
            :label="__('Inbox')"
            :options="inboxOptions"
            :model-value="inboxId"
            @update:model-value="(v) => (inboxId = Number(v))"
          />

          <FormControl
            v-if="inbox?.can_reply"
            v-model="text"
            type="textarea"
            :label="__('Message')"
            :rows="4"
          />

          <template v-else-if="inbox">
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Outside the 24-hour window, WhatsApp only accepts a template approved by Meta.',
                )
              }}
            </p>
            <p
              v-if="!inbox.templates.length"
              class="text-p-base text-ink-gray-7"
            >
              {{ __('This number has no approved text template.') }}
            </p>
            <template v-else>
              <FormControl
                type="select"
                :label="__('Template')"
                :options="templateOptions"
                :model-value="templateKey"
                @update:model-value="(v) => (templateKey = v)"
              />
              <FormControl
                v-for="variable in template?.variables || []"
                :key="variable"
                v-model="variables[variable]"
                :label="`{{${variable}}}`"
              />
              <div
                v-if="template"
                class="whitespace-pre-wrap rounded bg-surface-gray-2 p-2 text-p-sm text-ink-gray-7"
              >
                {{ preview }}
              </div>
            </template>
          </template>
        </template>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <ErrorMessage :message="sendError" />
        <div class="flex gap-2">
          <Button
            v-if="sent"
            :label="__('Open in SmartChat')"
            :link="sent.conversation_url"
          />
          <Button
            :label="sent ? __('Close') : __('Cancel')"
            @click="open = false"
          />
          <Button
            v-if="!sent && inbox"
            variant="solid"
            :label="__('Send')"
            :loading="sending"
            :disabled="!canSend"
            @click="send"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

// WhatsApp from the card goes out through the company's SmartChat; the
// seller picks the inbox (credtech#211). Inside the 24-hour window, or on a
// QR Code number, free text; otherwise an approved template.
const props = defineProps({
  deal: { type: String, required: true },
  phone: { type: String, required: true },
  name: { type: String, default: '' },
})
const emit = defineEmits(['sent'])
const open = defineModel('open', { type: Boolean, default: false })

const options = createResource({
  url: 'cred_hub.whatsapp_send.get_whatsapp_options',
  makeParams: () => ({ deal: props.deal, phone: props.phone }),
  onSuccess: (data) => {
    inboxId.value = data?.inboxes?.[0]?.id || null
  },
})

const inboxId = ref(null)
const text = ref('')
const templateKey = ref('')
const variables = reactive({})
const sending = ref(false)
const sendError = ref('')
const sent = ref(null)

watch(
  open,
  (value) => {
    if (!value) return
    sent.value = null
    sendError.value = ''
    text.value = ''
    options.fetch()
  },
  { immediate: true },
)

const inboxes = computed(() => options.data?.inboxes || [])
const inbox = computed(() => inboxes.value.find((i) => i.id === inboxId.value))
const inboxOptions = computed(() =>
  inboxes.value.map((i) => ({
    label: [i.name, i.kind === 'qr' ? __('QR Code') : i.phone]
      .filter(Boolean)
      .join(' · '),
    value: i.id,
  })),
)

const templateOptions = computed(() =>
  (inbox.value?.templates || []).map((t) => ({
    label: `${t.name} (${t.language})`,
    value: `${t.name}|${t.language}`,
  })),
)
const template = computed(() =>
  (inbox.value?.templates || []).find(
    (t) => `${t.name}|${t.language}` === templateKey.value,
  ),
)
watch(inbox, () => {
  templateKey.value = templateOptions.value[0]?.value || ''
})
const preview = computed(() =>
  (template.value?.body || '').replace(
    /{{\s*([\w.]+)\s*}}/g,
    (match, key) => variables[key] || match,
  ),
)

const canSend = computed(() => {
  if (!inbox.value) return false
  if (inbox.value.can_reply) return Boolean(text.value.trim())
  return Boolean(
    template.value &&
    template.value.variables.every((v) => (variables[v] || '').trim()),
  )
})

async function send() {
  sending.value = true
  sendError.value = ''
  try {
    let params = {
      deal: props.deal,
      phone: props.phone,
      name: props.name,
      inbox_id: inbox.value.id,
    }
    if (inbox.value.can_reply) params.text = text.value
    else
      Object.assign(params, {
        template_name: template.value.name,
        template_language: template.value.language,
        variables: JSON.stringify(
          Object.fromEntries(
            template.value.variables.map((v) => [v, variables[v]]),
          ),
        ),
      })
    sent.value = await call('cred_hub.whatsapp_send.send_whatsapp', params)
    toast.success(__('WhatsApp sent'))
    emit('sent', sent.value)
  } catch (e) {
    sendError.value =
      e?.messages?.[0] || e?.message || __('Could not send the message')
  } finally {
    sending.value = false
  }
}
</script>
