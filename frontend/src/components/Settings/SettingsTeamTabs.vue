<template>
  <!-- Figma "Configurações · Equipe" (2323:15708 / 2335:9297): "Abas" Pessoas
       and Hierarquia on top of the Users and Sales Hierarchy panels. 14
       Medium, 10px/4px padding, 24px apart, 2px blue line on the active one. -->
  <nav
    class="flex shrink-0 items-start gap-6 border-b border-[var(--ct-border)]"
  >
    <router-link
      v-for="tab in tabs"
      :key="tab.page"
      :to="settingsRoute(tab.page)"
      class="flex flex-col"
      :aria-current="tab.page === active ? 'page' : undefined"
    >
      <span
        class="px-1 py-2.5 text-[14px] font-medium leading-5"
        :class="
          tab.page === active
            ? 'text-[color:var(--ct-text-accent)]'
            : 'text-[color:var(--ct-text-secondary)] hover:text-[color:var(--ct-text-primary)]'
        "
      >
        {{ tab.label }}
      </span>
      <span
        class="h-0.5 w-full"
        :class="tab.page === active ? 'bg-[var(--ct-accent)]' : ''"
      />
    </router-link>
  </nav>
</template>

<script setup>
import { settingsRoute } from '@/composables/settingsNavigation'

defineProps({
  // 'Users' or 'Sales Hierarchy' (keys of settingsSections.js)
  active: { type: String, required: true },
})

const tabs = [
  { page: 'Users', label: __('People') },
  { page: 'Sales Hierarchy', label: __('Hierarchy') },
]
</script>
