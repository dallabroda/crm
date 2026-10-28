<template>
  <div class="flex flex-col gap-3" data-testid="form-preview">
    <div
      v-for="field in shown"
      :key="field.fieldname"
      class="flex items-center gap-3"
      :data-field="field.fieldname"
    >
      <div
        class="flex w-48 shrink-0 items-center gap-1 text-base text-ink-gray-7"
      >
        <span class="truncate">{{ __(field.label) }}</span>
        <span v-if="field.required === 1" class="text-ink-red-4">*</span>
        <Tooltip v-if="field.locked" :text="__('Always shown')">
          <span class="lucide-lock size-3 shrink-0 text-ink-gray-5" />
        </Tooltip>
      </div>
      <div
        class="flex h-7 min-w-0 flex-1 items-center rounded border border-outline-gray-2 bg-surface-gray-1 px-2 text-sm text-ink-gray-4"
      >
        <span class="truncate">{{ fieldTypeLabel(field) }}</span>
      </div>
      <div class="flex w-40 shrink-0 flex-wrap gap-1">
        <Badge
          v-if="field.is_created"
          :label="__('Created')"
          variant="subtle"
          theme="gray"
        />
        <Badge
          v-if="varies(field)"
          :label="__('Varies by stage')"
          variant="subtle"
          theme="orange"
        />
        <Badge
          v-if="field.read_only_rule === 1"
          :label="__('Read only')"
          variant="subtle"
          theme="gray"
        />
      </div>
    </div>
    <p v-if="hidden" class="text-p-sm text-ink-gray-5">
      {{
        hidden === 1
          ? __('1 field of the funnel is hidden here.')
          : __('{0} fields of the funnel are hidden here.', [hidden])
      }}
    </p>
  </div>
</template>

<script setup>
import { fieldTypeLabel } from '../Fields/fieldTypes'
import { Badge, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // crm.api.forms.get_form_schema().fields
  fields: { type: Array, default: () => [] },
})

// all stages: a field hidden only in some stages is shown, marked as varying
const shown = computed(() => props.fields.filter((f) => f.visible !== 0))
const hidden = computed(() => props.fields.length - shown.value.length)

function varies(field) {
  return (
    field.visible === null ||
    field.required === null ||
    field.read_only_rule === null
  )
}
</script>
