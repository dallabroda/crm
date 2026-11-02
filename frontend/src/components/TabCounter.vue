<template>
  <!-- Figma "Contador" (959:76) next to a tab label: the active tab uses the
       accent tone, the others the neutral one. Hidden while there is no count. -->
  <span
    v-if="value"
    class="inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs leading-4"
    :class="
      active
        ? 'bg-[var(--ct-accent-soft)] font-semibold text-[color:var(--ct-text-accent)]'
        : 'bg-[var(--ct-bg-panel)] text-ink-gray-9'
    "
  >
    {{ value }}
  </span>
</template>

<script setup>
import { computed, unref } from 'vue'

const props = defineProps({
  // pages pass the tab's `count`, often a computed ref
  count: { type: [Number, String, Object], default: 0 },
  active: { type: Boolean, default: false },
})

const value = computed(() => unref(props.count))
</script>
