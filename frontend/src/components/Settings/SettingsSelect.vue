<template>
  <!-- Figma "Filtro" (1165:20747) as the control of a settings row
       ("Configurações · Empresa" 2323:14221): sized by its text, label in
       Uso/Texto/Principal and a 16px chevron. -->
  <Dropdown :options="items" align="end">
    <template #default="{ open }">
      <button type="button" class="ct-filter" :disabled="disabled">
        <span class="truncate">{{ selectedLabel }}</span>
        <span
          class="size-4 shrink-0 text-[color:var(--ct-text-secondary)]"
          :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          aria-hidden="true"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import { Dropdown } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  // [{ label, value }] or plain values
  options: { type: Array, default: () => [] },
  placeholder: { type: [String, Number], default: '' },
  disabled: { type: Boolean, default: false },
})
const model = defineModel({ type: [String, Number], default: null })

const normalized = computed(() =>
  props.options
    .map((o) => (typeof o === 'object' ? o : { label: String(o), value: o }))
    .filter((o) => o.value !== '' && o.value != null),
)

const selectedLabel = computed(() => {
  const option = normalized.value.find((o) => o.value == model.value)
  return option ? option.label : props.placeholder
})

const items = computed(() =>
  normalized.value.map((o) => ({
    label: o.label,
    selected: o.value == model.value,
    onClick: () => {
      if (o.value != model.value) model.value = o.value
    },
  })),
)
</script>
