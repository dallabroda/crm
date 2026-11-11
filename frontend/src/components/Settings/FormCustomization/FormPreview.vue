<template>
  <!-- Figma "Campos" of "Prévia do formulário" (2324:15315): rows 8px apart,
       a 192px label (14 Regular, red *, 12px lock), a 48px gray box with the
       type in 16 gray and the "Varia por etapa" pills in a 112px column -->
  <div class="flex flex-col gap-2" data-testid="form-preview">
    <div
      v-for="field in shown"
      :key="field.fieldname"
      class="flex items-center gap-4"
      :data-field="field.fieldname"
    >
      <div
        class="flex w-48 shrink-0 items-center gap-1 text-[14px] leading-5 text-[var(--ct-text-primary)]"
      >
        <span class="truncate">{{ __(field.label) }}</span>
        <span v-if="field.required === 1" class="text-[var(--ct-error)]">
          *
        </span>
        <Tooltip v-if="field.locked" :text="__('Always shown')">
          <span class="lucide-lock size-3 shrink-0 text-ink-gray-9" />
        </Tooltip>
      </div>
      <div
        class="flex h-12 min-w-0 flex-1 items-center rounded-[6px] border border-[var(--ct-border)] bg-[var(--ct-bg-soft)] px-3.5 text-[16px] leading-6 text-[var(--ct-text-tertiary)]"
      >
        <span class="truncate">{{ fieldTypeLabel(field) }}</span>
      </div>
      <div class="flex w-28 shrink-0 flex-wrap gap-1">
        <span v-if="field.is_created" class="ct-pill">
          {{ __('Created') }}
        </span>
        <span v-if="varies(field)" class="ct-pill">
          {{ __('Varies by stage') }}
        </span>
        <span v-if="field.read_only_rule === 1" class="ct-pill">
          {{ __('Read only') }}
        </span>
      </div>
    </div>
    <p v-if="hidden" class="text-p-sm text-ink-gray-5">
      {{
        inFunnel
          ? hidden === 1
            ? __('1 field of the funnel is hidden here.')
            : __('{0} fields of the funnel are hidden here.', [hidden])
          : hidden === 1
            ? __('1 field is hidden in this form.')
            : __('{0} fields are hidden in this form.', [hidden])
      }}
    </p>
  </div>
</template>

<script setup>
import { fieldTypeLabel } from '../Fields/fieldTypes'
import '../settingsTable.css'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // crm.api.forms.get_form_schema().fields
  fields: { type: Array, default: () => [] },
  // cards: the hidden fields are the funnel's; organizations and contacts: the form's
  inFunnel: { type: Boolean, default: true },
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
