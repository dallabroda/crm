<template>
  <component
    :is="icon"
    width="16"
    height="16"
    class="text-ink-gray-7"
    :aria-label="status"
  />
</template>
<script setup>
// Style Guide: the task status is a Lucide circle at 1.4px ("Ícone/circle"
// on an open task in Figma "Card · Tarefas"); the other states use the same
// circle family.
import { computed } from 'vue'
import LucideCircle from '~icons/lucide/circle'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideCircleDashed from '~icons/lucide/circle-dashed'
import LucideCircleDot from '~icons/lucide/circle-dot'
import LucideCircleX from '~icons/lucide/circle-x'

const props = defineProps({
  status: { type: String, required: true },
})

const ICONS = {
  Backlog: LucideCircleDashed,
  Todo: LucideCircle,
  'In Progress': LucideCircleDot,
  Done: LucideCircleCheck,
  Canceled: LucideCircleX,
}

const icon = computed(() => ICONS[props.status] || LucideCircle)
</script>
