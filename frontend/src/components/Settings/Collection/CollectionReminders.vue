<template>
  <SettingsLayoutBase
    :title="__('Crédito e cobrança')"
    :description="
      __(
        'Approved WhatsApp templates sent through SmartChat to the sacado of each open título of the collection funnel, on the days you choose. The AI agent that answers and the templates are configured in SmartChat.',
      )
    "
  >
    <!-- the tabs of "Crédito e cobrança" (no sub-items in the menu) -->
    <template #header-top>
      <CreditTabs active="page:collection-reminders" />
    </template>
    <template #header-actions>
      <div v-if="loaded" class="flex gap-2">
        <Badge
          v-if="changed"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
        <Button
          v-if="changed"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="fill(saved)"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="saving"
          :disabled="!changed || (form.enabled && !complete)"
          @click="save"
        />
      </div>
    </template>
    <template #content>
      <!-- Figma "[HubTech CRM] · credtech#367 · Configurações › Régua de cobrança"
           (review page 1979:3291): same rhythm as Integração com ERP; the
           blocks are 950px wide at most (Figma 2493:4678) -->
      <div class="flex max-w-[950px] flex-col gap-6 pb-12">
        <CtAlert v-if="!chat.loading && !chat.connected" type="warning">
          {{
            __(
              'Connect your SmartChat in Settings › Lead Sources (SmartChat box) to use the collection reminders.',
            )
          }}
        </CtAlert>
        <CtAlert v-else-if="chat.error" type="error">{{ chat.error }}</CtAlert>

        <template v-if="loaded">
          <!-- On/off, cost estimate and WhatsApp number (Figma 2493:4678) -->
          <section class="flex flex-col gap-6">
            <div class="flex items-center justify-between gap-6">
              <div class="flex flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ __('Collection reminders') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'Every day at 9h. Never sent to a título that is protested, paid or closed, or has a payment promise or an agreement.',
                    )
                  }}
                </span>
              </div>
              <!-- never stuck ON: a disconnected SmartChat must not keep the reminders on -->
              <Switch
                v-model="form.enabled"
                size="md"
                :disabled="!chat.connected && !form.enabled"
              />
            </div>
            <CtAlert type="info">
              {{
                __(
                  'Meta charges each template sent. With the saved steps, about {0} messages in the next {1} days.',
                  [
                    (saved.estimate ?? 0).toLocaleString('pt-BR'),
                    saved.estimate_days ?? 30,
                  ],
                )
              }}
            </CtAlert>
            <div class="ct-field-48 w-[352px] max-w-full">
              <FormControl
                type="select"
                :label="__('WhatsApp number')"
                :placeholder="__('Select')"
                :options="inboxOptions"
                :model-value="form.inbox_id"
                @update:model-value="pickInbox"
              />
            </div>
          </section>

          <SettingsDivider />

          <!-- Steps: one white card per step, 12px apart -->
          <section class="flex flex-col gap-6">
            <div class="flex items-center justify-between gap-6">
              <div class="flex max-w-[662px] flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ __('Steps') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'Create as many messages as you want: each step is sent a few days before or after the due date (e.g. 5 days before, 3 days before, 2 days after). Each step goes once per título.',
                    )
                  }}
                </span>
              </div>
              <Button
                variant="outline"
                class="ct-btn-accent-text shrink-0 !h-12 !px-7 !text-[16px] !font-medium"
                :label="__('Add more steps')"
                :disabled="!inbox"
                @click="addStep"
              />
            </div>

            <p
              v-if="inbox && !inbox.templates.length"
              class="text-base leading-5 text-ink-gray-6"
            >
              {{
                __(
                  'This number has no approved text template yet. Create one in SmartChat › Settings › Templates and wait for Meta to approve it.',
                )
              }}
            </p>
            <p
              v-if="!form.steps.length"
              class="text-base leading-5 text-ink-gray-6"
            >
              {{ __('No step yet.') }}
            </p>

            <div v-if="form.steps.length" class="flex flex-col gap-3">
              <!-- columns: Dias 120 · Quando 260 · Mensagem · Excluir; the
                   template variables line up under them two by two -->
              <div
                v-for="(step, index) in form.steps"
                :key="step.key"
                class="ct-field-48 grid grid-cols-[120px_260px_minmax(0,1fr)_auto] items-end gap-4 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] p-4"
              >
                <FormControl
                  v-model="step.days"
                  type="number"
                  min="0"
                  :label="__('Days')"
                />
                <FormControl
                  v-model="step.when"
                  type="select"
                  :label="__('When')"
                  :options="whenOptions"
                />
                <FormControl
                  type="select"
                  :label="__('Approved message template')"
                  :placeholder="__('Select')"
                  :options="templateOptions"
                  :model-value="step.template"
                  @update:model-value="(value) => pickTemplate(step, value)"
                />
                <Button
                  variant="subtle"
                  theme="red"
                  class="!h-12 !px-7 !text-[16px] !font-semibold !text-[color:var(--ct-danger)]"
                  :label="__('Delete')"
                  @click="form.steps.splice(index, 1)"
                />

                <CtAlert
                  v-if="duplicateDays.has(signedDays(step))"
                  type="error"
                  class="col-span-full"
                >
                  {{ __('Two steps on the same day ({0}).', [stepDay(step)]) }}
                </CtAlert>
                <CtAlert
                  v-if="step.template && !templateOf(step)"
                  type="warning"
                  class="col-span-full"
                >
                  {{
                    __(
                      'The template {0} is no longer approved for this WhatsApp number. Choose another one.',
                      [step.template.split('|')[0]],
                    )
                  }}
                </CtAlert>
                <template v-if="templateOf(step)">
                  <FormControl
                    v-for="(variable, i) in templateOf(step).variables"
                    :key="variable"
                    :class="
                      i % 2 ? 'col-start-3 col-end-4' : 'col-start-1 col-end-3'
                    "
                    type="select"
                    :label="placeholder(variable)"
                    :options="variableOptions"
                    :model-value="step.variables[i] || ''"
                    @update:model-value="(key) => (step.variables[i] = key)"
                  />
                  <p
                    class="col-span-full whitespace-pre-wrap text-base text-ink-gray-6"
                  >
                    {{ templateOf(step).body }}
                  </p>
                </template>
              </div>
            </div>
          </section>
        </template>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import CreditTabs from '@/components/Settings/CreditBureaus/CreditTabs.vue'
import '../fieldOutline.css'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import CtAlert from '@/components/CtAlert.vue'
import { chat, loadChat } from '@/components/Settings/LeadSyncing/welcomeApi'
import { getRequest } from '@/components/Settings/LeadSyncing/metaLeadsApi'
import { Badge, Button, FormControl, Switch, call, toast } from 'frappe-ui'
import { computed, onMounted, reactive, ref } from 'vue'

// Régua de cobrança (credtech#367), served by cred_hub.collection.reminders
const API = 'cred_hub.collection.reminders.'

const loaded = ref(false)
const saving = ref(false)
const saved = ref({})
const variables = ref([])
// step.template: "<name>|<language>", one select for both
const form = reactive({ enabled: false, inbox_id: '', steps: [] })
let nextKey = 0

const inbox = computed(() =>
  chat.inboxes.find((i) => String(i.id) === String(form.inbox_id)),
)
// +5511999990000 -> +55 11 99999-0000
function formatPhone(phone) {
  let m = /^\+55(\d{2})(\d{4,5})(\d{4})$/.exec(phone || '')
  return m ? `+55 ${m[1]} ${m[2]}-${m[3]}` : phone
}

const inboxOptions = computed(() =>
  chat.inboxes.map((i) => ({
    label: i.phone ? `${i.name} (${formatPhone(i.phone)})` : i.name,
    value: String(i.id),
  })),
)
const templateOptions = computed(() =>
  (inbox.value?.templates || []).map((t) => ({
    label: `${t.name} (${t.language})`,
    value: `${t.name}|${t.language}`,
  })),
)
const variableOptions = computed(() => [
  { label: __('Choose the título information'), value: '' },
  ...variables.value.map((v) => ({ label: v.label, value: v.key })),
])

// The backend keeps signed days (-2 = two days before the due date); the
// screen shows them as "Dias" + "Quando" (Figma 2493:4678). 0 is the due date.
const whenOptions = computed(() => [
  { label: __('before the due date'), value: 'before' },
  { label: __('after the due date'), value: 'after' },
])

function signedDays(step) {
  let days = Math.abs(Number(step.days) || 0)
  return step.when === 'before' ? -days : days
}

function splitDays(days) {
  days = Number(days) || 0
  return { days: Math.abs(days), when: days < 0 ? 'before' : 'after' }
}

// "5 antes do vencimento", for the repeated-day error
function stepDay(step) {
  let when = whenOptions.value.find((o) => o.value === step.when)
  return `${Math.abs(Number(step.days) || 0)} ${when?.label || ''}`.trim()
}

function templateOf(step) {
  return inbox.value?.templates.find(
    (t) => `${t.name}|${t.language}` === step.template,
  )
}

const duplicateDays = computed(() => {
  let seen = new Set()
  let repeated = new Set()
  form.steps.forEach((step) => {
    let days = signedDays(step)
    ;(seen.has(days) ? repeated : seen).add(days)
  })
  return repeated
})

const complete = computed(
  () =>
    Boolean(inbox.value) &&
    form.steps.length > 0 &&
    duplicateDays.value.size === 0 &&
    form.steps.every((step) => {
      let template = templateOf(step)
      return (
        template &&
        step.days !== '' &&
        template.variables.every((_, i) => step.variables[i])
      )
    }),
)

function payload() {
  return {
    enabled: form.enabled ? 1 : 0,
    inbox_id: form.inbox_id ? Number(form.inbox_id) : null,
    steps: form.steps.map((step) => {
      let [name, language] = step.template ? step.template.split('|') : ['', '']
      let template = templateOf(step)
      return {
        days: signedDays(step),
        template_name: name || null,
        template_language: language || null,
        variables: template
          ? template.variables.map((_, i) => step.variables[i] || '')
          : [...step.variables],
      }
    }),
  }
}

const changed = computed(
  () =>
    loaded.value &&
    JSON.stringify(payload()) !== JSON.stringify(saved.value.payload),
)

// as written in the template body: {{1}} or {{name}}
function placeholder(variable) {
  return '{' + '{' + variable + '}' + '}'
}

function pickInbox(value) {
  form.inbox_id = value
  form.steps.forEach((step) => {
    step.template = ''
    step.variables = []
  })
}

function pickTemplate(step, value) {
  step.template = value
  step.variables = []
}

function addStep() {
  let last = form.steps[form.steps.length - 1]
  form.steps.push({
    key: nextKey++,
    ...splitDays(last ? signedDays(last) + 5 : 1),
    template: '',
    variables: [],
  })
}

function fill(data) {
  form.enabled = Boolean(data.enabled)
  form.inbox_id = data.inbox_id ? String(data.inbox_id) : ''
  form.steps = (data.steps || []).map((step) => ({
    key: nextKey++,
    ...splitDays(step.days),
    template: step.template_name
      ? `${step.template_name}|${step.template_language || ''}`
      : '',
    variables: [...(step.variables || [])],
  }))
  variables.value = data.variables || variables.value
  saved.value = { ...data, payload: payload() }
}

async function load() {
  try {
    await loadChat()
    fill(await getRequest(API + 'get_reminders'))
    loaded.value = true
  } catch (e) {
    toast.error(
      e?.messages?.[0] || __('Could not load the collection reminders'),
    )
  }
}

async function save() {
  saving.value = true
  try {
    fill(await call(API + 'save_reminders', payload()))
    toast.success(
      form.enabled
        ? __('Collection reminders on')
        : __('Collection reminders saved'),
    )
  } catch (e) {
    toast.error(
      e?.messages?.[0] || __('Could not save the collection reminders'),
    )
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
/* Figma "Campo" Seleção: white with the #dcdde2 border, like the text fields
   (fieldOutline.css covers input/select/textarea; frappe-ui's select is a button) */
.ct-field-48 :deep(button[data-slot='trigger']) {
  background-color: var(--ct-bg-page);
  border-color: var(--ct-border);
}
.ct-field-48 :deep(button[data-slot='trigger'][data-state='open']),
.ct-field-48 :deep(button[data-slot='trigger']:focus-visible) {
  border-color: var(--ct-border-strong);
}
</style>
