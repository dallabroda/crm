<template>
  <!-- Figma "Paginação" (1143:26666): "Mostrando X–Y de Z <itens>" on the
       left; first / previous / current page / next / last on the right. -->
  <div class="flex h-[54px] items-center justify-between gap-4">
    <div class="truncate text-[14px] leading-5 text-[var(--ct-text-secondary)]">
      {{ summary }}
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button
        v-for="nav in navBefore"
        :key="nav.icon"
        type="button"
        class="ct-page-nav"
        :disabled="nav.disabled"
        :aria-label="nav.label"
        :title="nav.label"
        @click="goToPage(nav.page)"
      >
        <span :class="nav.icon" class="size-4" aria-hidden="true" />
      </button>
      <div class="flex items-center gap-2">
        <span
          class="rounded-[var(--ct-radius-sm)] bg-[var(--ct-action-neutral)] px-3 py-0.5 text-[14px] leading-5 text-[var(--ct-text-primary)]"
        >
          {{ page }}
        </span>
        <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
          {{ pages === 1 ? __('of {0} page', [pages]) : __('of {0} pages', [pages]) }}
        </span>
      </div>
      <button
        v-for="nav in navAfter"
        :key="nav.icon"
        type="button"
        class="ct-page-nav"
        :disabled="nav.disabled"
        :aria-label="nav.label"
        :title="nav.label"
        @click="goToPage(nav.page)"
      >
        <span :class="nav.icon" class="size-4" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>
<script setup>
// Pages through the list resource with get_data's `start`. Filters, sorting
// and view changes rebuild the params without `start`, so they go back to page 1.
import { computed } from 'vue'

const DEFAULT_PAGE_LENGTH = 20

const props = defineProps({
  // the list resource (createResource of crm.api.doc.get_data)
  list: { type: Object, required: true },
  // plural noun after the count, already translated ("cards", "contatos")
  itemLabel: { type: String, default: '' },
})

const data = computed(() => props.list?.data || {})
const pageSize = computed(
  () => data.value.page_length_count || DEFAULT_PAGE_LENGTH,
)
const total = computed(() => data.value.total_count || 0)
const start = computed(() => data.value.start || 0)
const page = computed(() => Math.floor(start.value / pageSize.value) + 1)
const pages = computed(() =>
  Math.max(1, Math.ceil(total.value / pageSize.value)),
)

const summary = computed(() => {
  const rows = data.value.row_count || 0
  const from = rows ? start.value + 1 : 0
  return __('Showing {0}–{1} of {2} {3}', [
    from,
    start.value + rows,
    total.value,
    props.itemLabel,
  ]).trim()
})

const navBefore = computed(() => [
  {
    icon: 'lucide-chevrons-left',
    label: __('First page'),
    page: 1,
    disabled: page.value <= 1,
  },
  {
    icon: 'lucide-chevron-left',
    label: __('Previous page'),
    page: page.value - 1,
    disabled: page.value <= 1,
  },
])
const navAfter = computed(() => [
  {
    icon: 'lucide-chevron-right',
    label: __('Next page'),
    page: page.value + 1,
    disabled: page.value >= pages.value,
  },
  {
    icon: 'lucide-chevrons-right',
    label: __('Last page'),
    page: pages.value,
    disabled: page.value >= pages.value,
  },
])

function goToPage(target) {
  const list = props.list
  if (!list || list.loading || target < 1 || target > pages.value) return
  list.params = {
    ...list.params,
    page_length: pageSize.value,
    page_length_count: pageSize.value,
    start: (target - 1) * pageSize.value,
  }
  list.reload()
}
</script>
