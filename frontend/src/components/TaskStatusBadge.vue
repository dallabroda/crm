<template>
  <!-- Figma "Tarefas · Lista" (809:2), "Pílula de status": a 6px dot and the
       status, both in the tone of its kanban column. -->
  <span
    v-if="status"
    class="inline-flex h-5 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 text-xs font-medium leading-4"
    :class="toneClass"
  >
    <span class="size-1.5 shrink-0 rounded-full bg-current" />
    {{ __(status) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: '' },
})

const TONES = {
  Backlog: 'bg-[var(--ct-warning-soft)] text-[color:var(--ct-warning)]',
  Todo: 'bg-[var(--ct-bg-panel)] text-ink-gray-9',
  'In Progress': 'bg-[var(--ct-accent-soft)] text-[color:var(--ct-accent)]',
  Done: 'bg-[var(--ct-success-soft)] text-[color:var(--ct-success)]',
  Canceled: 'bg-[var(--ct-error-soft)] text-[color:var(--ct-error)]',
}

const toneClass = computed(() => TONES[props.status] || TONES.Todo)
</script>
