<template>
  <div
    class="flex items-center justify-between gap-4 rounded border px-4 py-3 text-p-sm"
    :class="tone"
  >
    <span>{{ text }}</span>
    <Button
      v-if="invoiceUrl"
      class="shrink-0"
      :label="__('Pay invoice')"
      icon-right="lucide-external-link"
      @click="openInvoice(invoiceUrl)"
    />
  </div>
</template>

<script setup>
import { openInvoice } from './planApi'
import { Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  theme: { type: String, default: 'gray' },
  // Asaas invoice page, where the card is typed
  invoiceUrl: { type: String, default: null },
})

const tone = computed(
  () =>
    ({
      red: 'border-outline-red-2 bg-surface-red-1 text-ink-red-4',
      orange: 'border-outline-amber-2 bg-surface-amber-1 text-ink-amber-4',
    })[props.theme] ||
    'border-outline-gray-1 bg-surface-gray-1 text-ink-gray-7',
)
</script>
