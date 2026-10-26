<template>
  <div class="flex flex-col rounded border border-outline-gray-1">
    <div class="flex items-center gap-3 px-3 py-2">
      <div class="flex min-w-0 flex-1 flex-col">
        <span class="truncate text-sm text-ink-gray-8">{{ form.name }}</span>
        <span class="text-p-xs text-ink-gray-5">
          {{
            form.last_lead_at
              ? __('Last lead {0}', [timeAgo(form.last_lead_at)])
              : __('No leads yet')
          }}
        </span>
      </div>
      <div class="w-56">
        <PipelineSelect
          :label="''"
          :model-value="form.pipeline"
          :disabled="saving"
          @update:model-value="(pipeline) => save({ pipeline })"
        />
      </div>
      <Button
        :label="__('Fields')"
        :icon-right="showMapping ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        variant="ghost"
        @click="showMapping = !showMapping"
      />
      <Button
        :label="__('WhatsApp')"
        :icon-right="showWelcome ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        variant="ghost"
        @click="showWelcome = !showWelcome"
      />
      <Tooltip
        :text="
          form.pipeline
            ? __('Receive leads from this form')
            : __('Choose the funnel first')
        "
      >
        <Switch
          :model-value="Boolean(form.enabled)"
          :disabled="saving || !form.pipeline"
          @update:model-value="(enabled) => save({ enabled: enabled ? 1 : 0 })"
        />
      </Tooltip>
    </div>

    <div
      v-if="showMapping"
      class="flex flex-col gap-2 border-t border-outline-gray-1 px-3 py-3"
    >
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Where each answer of the form goes in the card. Unmapped answers are kept in the card notes.',
          )
        }}
      </p>
      <div
        v-for="question in form.questions"
        :key="question.key"
        class="grid grid-cols-2 items-center gap-3"
      >
        <span class="truncate text-sm text-ink-gray-7">
          {{ question.label || question.key }}
        </span>
        <FormControl
          type="select"
          :options="leadFieldOptions"
          :model-value="mapping[question.key] || ''"
          :disabled="saving"
          @update:model-value="(field) => (mapping[question.key] = field)"
        />
      </div>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="__('Save fields')"
          :loading="saving"
          :disabled="!mappingChanged"
          @click="save({ mapping: { ...mapping } })"
        />
      </div>
    </div>
    <WelcomeMessage v-if="showWelcome" :source="`facebook:${form.id}`" />
  </div>
</template>

<script setup>
import PipelineSelect from '@/components/Pipelines/PipelineSelect.vue'
import WelcomeMessage from './WelcomeMessage.vue'
import { metaLeadsApi } from './metaLeadsApi'
import { getMeta } from '@/stores/meta'
import { timeAgo } from '@/utils'
import { Button, FormControl, Switch, Tooltip, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  form: { type: Object, required: true },
})

const emit = defineEmits(['changed'])

const saving = ref(false)
const showMapping = ref(false)
const showWelcome = ref(false)

const savedMapping = () =>
  Object.fromEntries(
    (props.form.questions || []).map((q) => [q.key, q.mapped_to || '']),
  )
const mapping = reactive(savedMapping())
const mappingChanged = computed(() => {
  let saved = savedMapping()
  return Object.keys(mapping).some((key) => mapping[key] !== saved[key])
})

const { getFields } = getMeta('CRM Lead')
const leadFieldOptions = computed(() => [
  { label: __('Not used'), value: '' },
  ...(getFields() || [])
    .filter((field) => field.fieldname && !field.read_only && !field.hidden)
    .map((field) => ({ label: __(field.label), value: field.fieldname })),
])

async function save(values) {
  saving.value = true
  try {
    await metaLeadsApi.saveForm(props.form.id, values)
    toast.success(__('Saved'))
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the form settings'))
  } finally {
    saving.value = false
  }
}
</script>
