<template>
  <div class="flex flex-col gap-1">
    <FormControl
      type="textarea"
      :label="__('Address of your website')"
      :placeholder="'https://www.suaempresa.com.br'"
      :rows="2"
      :disabled="disabled"
      :model-value="modelValue"
      @update:model-value="(v) => emit('update:modelValue', v)"
    />
    <p
      class="text-p-sm"
      :class="
        modelValue && !validOrigins(modelValue)
          ? 'text-ink-red-6'
          : 'text-ink-gray-5'
      "
    >
      {{
        __(
          'Leads are accepted only from these addresses, one per line, starting with https://. Include the version with and without www if your site uses both.',
        )
      }}
    </p>
  </div>
</template>

<script>
// One address per line, each a whole http(s) origin (no path needed)
export function validOrigins(text) {
  let lines = String(text || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
  return (
    lines.length > 0 &&
    lines.every((line) => {
      try {
        let url = new URL(line)
        return ['http:', 'https:'].includes(url.protocol) && Boolean(url.host)
      } catch {
        return false
      }
    })
  )
}
</script>

<script setup>
import { FormControl } from 'frappe-ui'

defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])
</script>
