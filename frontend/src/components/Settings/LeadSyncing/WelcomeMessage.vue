<template>
  <div class="flex flex-col gap-3 border-t border-outline-gray-1 px-3 py-3">
    <div class="flex items-center justify-between gap-4">
      <div class="flex flex-col gap-0.5">
        <span class="text-sm font-medium text-ink-gray-8">
          {{ __('WhatsApp welcome message') }}
        </span>
        <span class="text-p-xs text-ink-gray-5">
          {{
            __(
              'Sent to each new lead of this source, from your WhatsApp number in Cred Chat.',
            )
          }}
        </span>
      </div>
      <Switch v-if="chat.connected" v-model="form.enabled" :disabled="saving" />
    </div>

    <p v-if="!chat.connected" class="text-p-sm text-ink-gray-6">
      {{
        __(
          'Connect your Cred Chat in the "Cred Chat" box, below the sources, to use it.',
        )
      }}
    </p>

    <template v-else-if="loaded">
      <div class="grid grid-cols-2 gap-3">
        <FormControl
          type="select"
          :label="__('WhatsApp number')"
          :options="inboxOptions"
          :model-value="form.inbox_id"
          :disabled="saving"
          @update:model-value="pickInbox"
        />
        <FormControl
          type="select"
          :label="__('Message (approved template)')"
          :options="templateOptions"
          :model-value="form.template"
          :disabled="saving || !inbox"
          @update:model-value="pickTemplate"
        />
      </div>
      <p
        v-if="inbox && !inbox.templates.length"
        class="text-p-sm text-ink-gray-6"
      >
        {{
          __(
            'This number has no approved text template yet. Create one in Cred Chat › Settings › Templates and wait for Meta to approve it.',
          )
        }}
      </p>

      <template v-if="template">
        <div
          class="whitespace-pre-wrap rounded bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-8"
        >
          {{ template.body }}
        </div>
        <div
          v-for="(variable, i) in template.variables"
          :key="variable"
          class="grid grid-cols-[8rem_1fr] items-center gap-3"
        >
          <code class="text-sm text-ink-gray-7">{{
            placeholder(variable)
          }}</code>
          <FormControl
            type="select"
            :options="fieldOptions"
            :model-value="form.variables[i] || ''"
            :disabled="saving"
            @update:model-value="(field) => (form.variables[i] = field)"
          />
        </div>
      </template>

      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Meta charges each conversation started by the company on your WhatsApp account. Leads without a valid mobile number get no message.',
          )
        }}
      </p>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Save welcome message')"
          :loading="saving"
          :disabled="!changed || (form.enabled && !complete)"
          @click="save"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { chat, welcomeApi } from './welcomeApi'
import { Button, FormControl, Switch, toast } from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'

const props = defineProps({
  // "facebook:<form id>" or the name of a Cred Hub Lead Source
  source: { type: String, required: true },
})

const loaded = ref(false)
const saving = ref(false)
const leadFields = ref([])
const saved = ref({})
// template: "<name>|<language>", one select for both
const form = reactive({
  enabled: false,
  inbox_id: '',
  template: '',
  variables: [],
})

const inbox = computed(() =>
  chat.inboxes.find((i) => String(i.id) === String(form.inbox_id)),
)
const template = computed(() =>
  inbox.value?.templates.find(
    (t) => `${t.name}|${t.language}` === form.template,
  ),
)

const inboxOptions = computed(() => [
  { label: '', value: '' },
  ...chat.inboxes.map((i) => ({
    label: i.phone ? `${i.name} (${i.phone})` : i.name,
    value: String(i.id),
  })),
])
const templateOptions = computed(() => [
  { label: '', value: '' },
  ...(inbox.value?.templates || []).map((t) => ({
    label: `${t.name} (${t.language})`,
    value: `${t.name}|${t.language}`,
  })),
])
const fieldOptions = computed(() => [
  { label: __('Choose a lead field'), value: '' },
  ...leadFields.value.map((f) => ({ label: f.label, value: f.fieldname })),
])

const complete = computed(
  () =>
    Boolean(template.value) &&
    template.value.variables.every((_, i) => form.variables[i]),
)
const changed = computed(
  () => JSON.stringify(payload()) !== JSON.stringify(saved.value),
)

// as written in the template body: {{1}} or {{name}}
function placeholder(variable) {
  return '{' + '{' + variable + '}' + '}'
}

function pickInbox(value) {
  form.inbox_id = value
  form.template = ''
  form.variables = []
}

function pickTemplate(value) {
  form.template = value
  form.variables = []
}

function payload() {
  let [name, language] = form.template ? form.template.split('|') : ['', '']
  return {
    enabled: form.enabled ? 1 : 0,
    inbox_id: form.inbox_id ? Number(form.inbox_id) : null,
    template_name: name || null,
    template_language: language || null,
    variables: template.value
      ? template.value.variables.map((_, i) => form.variables[i] || '')
      : [],
  }
}

function fill(welcome) {
  form.enabled = Boolean(welcome.enabled)
  form.inbox_id = welcome.inbox_id ? String(welcome.inbox_id) : ''
  // a record saved while off may lack the language: take the template's own
  let language =
    welcome.template_language ||
    inbox.value?.templates.find((t) => t.name === welcome.template_name)
      ?.language ||
    ''
  form.template = welcome.template_name
    ? `${welcome.template_name}|${language}`
    : ''
  form.variables = [...(welcome.variables || [])]
  leadFields.value = welcome.lead_fields || []
  saved.value = payload()
}

async function load() {
  if (!chat.connected) return
  try {
    fill(await welcomeApi.get(props.source))
    loaded.value = true
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the welcome message'))
  }
}

async function save() {
  saving.value = true
  try {
    fill(await welcomeApi.save(props.source, payload()))
    toast.success(
      form.enabled
        ? __('Welcome message on for this source')
        : __('Welcome message saved'),
    )
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the welcome message'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
// connected after this panel was opened, or disconnected (which turns every
// source off): read the settings again on the next connection
watch(
  () => chat.connected,
  (connected) => (connected ? load() : (loaded.value = false)),
)
</script>
