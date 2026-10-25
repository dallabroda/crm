<template>
  <Tooltip :text="tooltip">
    <button
      type="button"
      class="size-6 rounded-4 text-xs-medium transition-colors"
      :class="
        active
          ? 'bg-surface-gray-7 text-ink-white'
          : 'bg-surface-gray-2 text-ink-gray-5 hover:bg-surface-gray-3'
      "
      :disabled="disabled"
      :aria-pressed="active"
      :aria-label="tooltip"
      @click="emit('toggle')"
    >
      {{ label }}
    </button>
  </Tooltip>
</template>
<script setup>
import { Tooltip } from 'frappe-ui'

defineProps({
  label: { type: String, required: true },
  tooltip: { type: String, default: '' },
  active: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle'])
</script>
