<template>
  <SettingsLayoutBase
    :title="__('Collection reminders')"
    :description="
      __(
        'Approved WhatsApp templates sent through SmartChat to the sacado of each open título of the collection funnel, on the days you choose. The AI agent that answers and the templates are configured in SmartChat.',
      )
    "
  >
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
           (review page 1979:3291): same rhythm as Integração com ERP -->
      <div class="flex flex-col gap-6 pb-12">
        <CtAlert v-if="!chat.loading && !chat.connected" type="warning">
          {{
            __(
              'Connect your SmartChat in Settings › Lead Sources (SmartChat box) to use the collection reminders.',
            )
          }}
        </CtAlert>
        <CtAlert v-else-if="chat.error" type="error">{{ chat.error }}</CtAlert>

        <template v-if="loaded">
          <!-- On/off and WhatsApp number -->
          <section class="flex flex-col gap-6">
            <div class="flex items-start justify-between gap-4">
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
              <Switch v-model="form.enabled" :disabled="!chat.connected" />
            </div>
            <div class="ct-field-48 grid grid-cols-2 gap-4">
              <FormControl
                type="select"
                :label="__('WhatsApp number')"
                :placeholder="__('Select')"
                :options="inboxOptions"
                :model-value="form.inbox_id"
                @update:model-value="pickInbox"
              />
            </div>
            <CtAlert type="info">
              {{
                __(
                  'Meta charges each template sent. With these steps, about {0} messages in the next {1} days.',
                  [saved.estimate ?? 0, saved.estimate_days ?? 30],
                )
              }}
            </CtAlert>
          </section>

          <SettingsDivider />

          <!-- Steps -->
          <section class="flex flex-col gap-6">
            <div class="flex items-start justify-between gap-4">
              <div class="flex flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ __('Steps') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'Days from the due date: -2 is two days before, 0 is the due date, 5 is five days after. Each step goes once per título.',
                    )
                  }}
                </span>
              </div>
              <Button
                :label="__('Add step')"
                :disabled="!inbox"
                @click="addStep"
              >
                <template #prefix><LucidePlus class="size-4" /></template>
              </Button>
            </div>

            <p
              v-if="inbox && !inbox.templates.length"
              class="text-p-sm text-ink-gray-6"
            >
              {{
                __(
                  'This number has no approved text template yet. Create one in SmartChat › Settings › Templates and wait for Meta to approve it.',
                )
              }}
            </p>
            <p v-if="!form.steps.length" class="text-p-sm text-ink-gray-6">
              {{ __('No step yet.') }}
            </p>

            <div
              v-for="(step, index) in form.steps"
              :key="step.key"
              class="flex flex-col gap-4 rounded-[var(--ct-radius-md)] border border-outline-gray-2 p-4"
            >
              <div
                class="ct-field-48 grid grid-cols-[10rem_1fr_auto] items-end gap-4"
              >
                <FormControl
                  v-model="step.days"
                  type="number"
                  :label="__('Days from the due date')"
                />
                <FormControl
                  type="select"
                  :label="__('Message (approved template)')"
                  :placeholder="__('Select')"
                  :options="templateOptions"
                  :model-value="step.template"
                  @update:model-value="(value) => pickTemplate(step, value)"
                />
                <Button
                  variant="ghost"
                  :aria-label="__('Remove step')"
                  @click="form.steps.splice(index, 1)"
                >
                  <LucideTrash2 class="size-4" />
                </Button>
              </div>
              <template v-if="templateOf(step)">
                <div
                  class="whitespace-pre-wrap rounded bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
                >
                  {{ templateOf(step).body }}
                </div>
                <div
                  v-for="(variable, i) in templateOf(step).variables"
                  :key="variable"
                  class="grid grid-cols-[8rem_1fr] items-center gap-3"
                >
                  <code class="text-sm text-ink-gray-7">{{
                    placeholder(variable)
                  }}</code>
                  <FormControl
                    type="select"
                    :options="variableOptions"
                    :model-value="step.variables[i] || ''"
                    @update:model-value="(key) => (step.variables[i] = key)"
                  />
                </div>
              </template>
            </div>
          </section>
        </template>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import '../fieldOutline.css'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import CtAlert from '@/components/CtAlert.vue'
import { chat, loadChat } from '@/components/Settings/LeadSyncing/welcomeApi'
import { getRequest } from '@/components/Settings/LeadSyncing/metaLeadsApi'
import LucidePlus from '~icons/lucide/plus'
import LucideTrash2 from '~icons/lucide/trash-2'
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
const inboxOptions = computed(() =>
  chat.inboxes.map((i) => ({
    label: i.phone ? `${i.name} (${i.phone})` : i.name,
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

function templateOf(step) {
  return inbox.value?.templates.find(
    (t) => `${t.name}|${t.language}` === step.template,
  )
}

const complete = computed(
  () =>
    Boolean(inbox.value) &&
    form.steps.length > 0 &&
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
        days: Number(step.days) || 0,
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
    days: last ? Number(last.days) + 5 : 1,
    template: '',
    variables: [],
  })
}

function fill(data) {
  form.enabled = Boolean(data.enabled)
  form.inbox_id = data.inbox_id ? String(data.inbox_id) : ''
  form.steps = (data.steps || []).map((step) => ({
    key: nextKey++,
    days: step.days,
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
