<template>
  <FormControl
    v-if="filter.fieldtype == 'Check'"
    v-model="filter.value"
    :label="filter.label"
    type="checkbox"
    @change.stop="updateFilter(filter, $event.target.checked)"
  />
  <!-- Figma "Filtros rápidos" (1185:15589): select and link filters are a
       "Filtro" (white, grey border, black text, chevron), the text ones a
       "Campo de busca". -->
  <Dropdown
    v-else-if="filter.fieldtype === 'Select'"
    :options="selectOptions"
  >
    <template #default="{ open }">
      <button type="button" class="ct-filter">
        <span class="truncate">{{ selectLabel || filter.label }}</span>
        <span
          class="size-4 shrink-0"
          :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          aria-hidden="true"
        />
      </button>
    </template>
  </Dropdown>
  <Link
    v-else-if="filter.fieldtype === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
  >
    <template #target="{ togglePopover, isOpen, selectedValue, displayValue }">
      <button type="button" class="ct-filter" @click="togglePopover()">
        <span class="truncate">
          {{ selectedValue ? displayValue(selectedValue) : filter.label }}
        </span>
        <span
          class="size-4 shrink-0"
          :class="isOpen ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          aria-hidden="true"
        />
      </button>
    </template>
  </Link>
  <component
    :is="filter.fieldtype === 'Date' ? DatePicker : DateTimePicker"
    v-else-if="['Date', 'Datetime'].includes(filter.fieldtype)"
    class="border-none"
    :model-value="filter.value"
    :placeholder="filter.label"
    :format="
      filter.fieldtype === 'Date'
        ? getFormat('', '', true, false, false)
        : getFormat('', '', true, true, false)
    "
    @change="(v) => updateFilter(filter, v)"
  />
  <label v-else class="ct-search">
    <span class="lucide-search size-4 shrink-0" aria-hidden="true" />
    <input
      v-model="filter.value"
      type="text"
      :placeholder="filter.label"
      @input.stop="debouncedFn(filter, $event.target.value)"
    />
  </label>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { Dropdown, FormControl, DatePicker, DateTimePicker } from 'frappe-ui'
import { getFormat } from '@/utils'
import { useDebounceFn } from '@vueuse/core'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  filter: { type: Object, required: true },
})

const filter = reactive(props.filter)

const emit = defineEmits(['applyQuickFilter'])

watch(
  () => props.filter,
  (newFilter) => Object.assign(filter, newFilter),
  { deep: true },
)

const selectLabel = computed(
  () =>
    filter.value &&
    (filter.options || []).find((o) => o.value === filter.value)?.label,
)

// The empty option clears the filter, shown as "Todos"
const selectOptions = computed(() =>
  (filter.options || []).map((option) => ({
    label: option.value ? option.label : __('All'),
    onClick: () => {
      filter.value = option.value
      updateFilter(filter, option.value)
    },
  })),
)

const debouncedFn = useDebounceFn((f, value) => {
  emit('applyQuickFilter', f, value)
}, 500)

function updateFilter(f, value) {
  emit('applyQuickFilter', f, value)
}
</script>
