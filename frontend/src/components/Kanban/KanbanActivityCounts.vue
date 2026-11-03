<template>
  <!-- Figma "Card de Kanban" (1215:1371), "Atividades": icon 14px + count 12px,
       12px between items; blue when there is activity, tertiary gray at zero -->
  <div class="flex items-center gap-3 text-xs leading-4">
    <Tooltip v-for="item in items" :key="item.tab" :text="item.tooltip">
      <button
        type="button"
        class="flex items-center gap-1 rounded bg-transparent p-0 cursor-pointer hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-4 focus-visible:ring-offset-1"
        :class="item.count ? 'text-[var(--ct-text-accent)]' : 'text-ink-gray-4'"
        :aria-label="item.tooltip"
        @click.stop.prevent="openTab(item.tab)"
      >
        <span :class="item.icon" class="size-3.5 shrink-0" aria-hidden="true" />
        <span>{{ item.count }}</span>
      </button>
    </Tooltip>
  </div>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { computed } from 'vue'

const props = defineProps({
  // route of the document the card belongs to; the tab is appended as hash
  route: {
    type: Object,
    required: true,
  },
  counts: {
    type: Object,
    default: () => ({}),
  },
})

const router = useRouter()

const items = computed(() =>
  [
    { tab: 'emails', icon: 'lucide-mail', label: __('Emails') },
    { tab: 'notes', icon: 'lucide-file-text', label: __('Notes') },
    { tab: 'tasks', icon: 'lucide-circle-check', label: __('Tasks') },
    { tab: 'comments', icon: 'lucide-message-circle', label: __('Comments') },
  ].map((item) => {
    let count = Number(props.counts[item.tab]) || 0
    return {
      ...item,
      count,
      tooltip: count ? `${count} ${item.label}` : item.label,
    }
  }),
)

function openTab(tab) {
  router.push({ ...props.route, hash: '#' + tab })
}
</script>
