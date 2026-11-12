<template>
  <!-- Figma "Aba" (Crédito e cobrança): 14 Medium, 4px/10px padding, 2px
       blue line on the active tab. One row for the whole "Crédito e
       cobrança" entry of the menu: the five tabs of the credit page and the
       Cartório, Régua and ERP pages, so the menu has no sub-items. -->
  <div
    class="flex shrink-0 items-start gap-4 overflow-x-auto border-b border-[var(--ct-border)] [&::-webkit-scrollbar]:h-0"
    role="tablist"
  >
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      role="tab"
      :aria-selected="active === tab.key"
      class="flex shrink-0 flex-col"
      @click="open(tab)"
    >
      <span
        class="whitespace-nowrap px-1 py-2.5 text-[14px] font-medium leading-5"
        :class="
          active === tab.key
            ? 'text-[var(--ct-accent)]'
            : 'text-[var(--ct-text-secondary)] hover:text-[var(--ct-text-primary)]'
        "
      >
        {{ tab.label }}
      </span>
      <span
        class="h-0.5 w-full"
        :class="active === tab.key ? 'bg-[var(--ct-accent)]' : ''"
      />
    </button>
  </div>
</template>

<script setup>
import { getSettingsSections } from '@/components/Settings/settingsSections'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // a tab of the credit page (funnels, bureaus, reports, policy, prefilter)
  // or "page:<slug>" for the other pages
  active: { type: String, required: true },
  // on the credit page itself its tabs switch in place
  inPage: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])
const router = useRouter()

const PAGE_TABS = [
  { slug: 'bureaus', label: 'Cartório e localização' },
  { slug: 'collection-reminders', label: 'Régua de cobrança' },
  { slug: 'erp-integration', label: 'Integração com ERP' },
]

const visibleSlugs = computed(
  () =>
    new Set(
      getSettingsSections().flatMap((s) => s.items.map((i) => i.slug)),
    ),
)

const tabs = computed(() => [
  ...(visibleSlugs.value.has('credit-compliance')
    ? [
        { key: 'funnels', label: __('Funis e documentos') },
        { key: 'bureaus', label: __('Bureaus e credenciais') },
        { key: 'reports', label: __('Relatórios por nível') },
        { key: 'policy', label: __('Dossiê e parecer da IA') },
        { key: 'prefilter', label: __('Pré-filtro e régua de corte') },
      ]
    : []),
  ...PAGE_TABS.filter((t) => visibleSlugs.value.has(t.slug)).map((t) => ({
    key: 'page:' + t.slug,
    slug: t.slug,
    label: __(t.label),
  })),
])

function open(tab) {
  if (tab.slug) {
    router.push({ name: 'Settings', params: { section: tab.slug } })
  } else if (props.inPage) {
    emit('select', tab.key)
  } else {
    router.push({
      name: 'Settings',
      params: { section: 'credit-compliance' },
      hash: '#' + tab.key,
    })
  }
}
</script>
