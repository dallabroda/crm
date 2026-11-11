<template>
  <!-- Figma "Modal · Enviar WhatsApp" (1737:24291; template 1885:26844):
       480px, contact line, Style Guide "Campo" fields; outside the 24-hour
       window an info alert, the template with its "Aprovado" pill, the
       variables side by side and a chat-bubble preview -->
  <Dialog v-model:open="open" size="ct-480" :title="__('Send WhatsApp')">
    <template #default>
      <div class="flex flex-col gap-4" data-testid="smartchat-whatsapp">
        <div class="text-base leading-5 text-ink-gray-6">
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
          <!-- Figma "Aviso · Janela de 24 h": Style Guide info alert, above
               the inbox, when only a template can go out -->
          <div
            v-if="inbox && !inbox.can_reply"
            class="flex items-start gap-2.5 rounded-[var(--ct-radius-md)] bg-[var(--ct-info-soft)] py-3 pl-3.5 pr-2.5 text-base font-medium leading-5 text-[color:var(--ct-info)]"
            role="note"
          >
            <span class="lucide-info size-5 shrink-0" aria-hidden="true" />
            {{ __('WhatsApp only accepts templates approved by Meta.') }}
          </div>
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
            :rows="3"
          />

          <template v-else-if="inbox">
            <p
              v-if="!inbox.templates.length"
              class="text-base leading-5 text-ink-gray-6"
            >
              {{ __('This number has no approved text template.') }}
            </p>
            <template v-else>
              <!-- template and variables are 80px Campos (6px under the box) -->
              <div class="relative pb-1.5">
                <FormControl
                  type="select"
                  :label="__('Template')"
                  :options="templateOptions"
                  :model-value="templateKey"
                  @update:model-value="(v) => (templateKey = v)"
                />
                <!-- Figma "Pílula · Aprovado": only approved templates are listed -->
                <Badge
                  v-if="template"
                  class="pointer-events-none absolute bottom-5 right-11 !bg-[var(--ct-success-soft)] !text-[color:var(--ct-success)]"
                  :label="__('Approved')"
                >
                  <template #prefix>
                    <span
                      class="size-1.5 rounded-full bg-[var(--ct-status-green)]"
                    />
                  </template>
                </Badge>
              </div>
              <div
                v-if="template?.variables?.length"
                class="grid grid-cols-3 gap-3 pb-1.5"
              >
                <FormControl
                  v-for="variable in template.variables"
                  :key="variable"
                  v-model="variables[variable]"
                  :label="`{{${variable}}}`"
                />
              </div>
              <!-- Figma "Prévia": the message as a sent bubble -->
              <div v-if="template" class="flex flex-col gap-1.5">
                <div class="ct-field-label">{{ __('Message preview') }}</div>
                <div
                  class="flex justify-end rounded-[var(--ct-radius-md)] bg-[var(--ct-bg-soft)] p-3"
                >
                  <div
                    class="flex max-w-[342px] flex-col gap-1 rounded-[8px_8px_2px_8px] border border-[var(--ct-border)] bg-surface-base px-2.5 pb-1.5 pt-2"
                  >
                    <div
                      class="whitespace-pre-wrap text-base leading-5 text-ink-gray-9"
                    >
                      {{ preview }}
                    </div>
                    <div
                      class="self-end text-xs font-medium leading-4 text-ink-gray-6"
                    >
                      {{ previewTime }}
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </template>
        </template>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <!-- the wrapper keeps the buttons on the right when there is no error -->
        <div><ErrorMessage :message="sendError" /></div>
        <div class="flex gap-3">
          <Button
            v-if="sent"
            variant="outline"
            :label="__('Open in SmartChat')"
            :href="sent.conversation_url"
          />
          <Button
            variant="outline"
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
  Badge,
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
// QR Code number, free text; otherwise an approved template. Also from the
// contact page, with `contact` instead of `deal` (credtech#258).
const props = defineProps({
  deal: { type: String, default: '' },
  contact: { type: String, default: '' },
  phone: { type: String, required: true },
  name: { type: String, default: '' },
})
const emit = defineEmits(['sent'])
const open = defineModel('open', { type: Boolean, default: false })

const options = createResource({
  url: 'cred_hub.whatsapp_send.get_whatsapp_options',
  makeParams: () => ({
    deal: props.deal || undefined,
    contact: props.contact || undefined,
    phone: props.phone,
  }),
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

// the bubble's time, as the message would be sent now
const previewTime = computed(() =>
  new Date().toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }),
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
      deal: props.deal || undefined,
      contact: props.contact || undefined,
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
