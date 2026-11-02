<template>
  <!-- Figma "Pílula" (959:69) for a task priority: High = error tone,
       Medium = warning tone, Low = neutral. -->
  <span
    v-if="priority"
    class="inline-flex h-5 shrink-0 items-center whitespace-nowrap rounded-full px-2.5 text-xs font-medium leading-4"
    :class="toneClass"
  >
    {{ __(priority) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  priority: { type: String, default: '' },
})

const TONES = {
  High: 'bg-[var(--ct-error-soft)] text-[color:var(--ct-error)]',
  Medium: 'bg-[var(--ct-warning-soft)] text-[color:var(--ct-warning)]',
  Low: 'bg-[var(--ct-bg-panel)] text-ink-gray-9',
}

const toneClass = computed(() => TONES[props.priority] || TONES.Low)
</script>
