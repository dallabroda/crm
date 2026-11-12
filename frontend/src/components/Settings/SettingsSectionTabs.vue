<template>
  <!-- Figma "Abas" (E-mail 2336:10121, Entrada de leads 2336:10624): 24px
       apart, 14/500 labels with 4px/10px padding, 2px blue line on the active
       tab, 1px line under the row. Each tab is a settings section. -->
  <div
    v-if="visibleTabs.length > 1"
    class="flex shrink-0 items-start gap-6 border-b border-[var(--ct-border)]"
    role="tablist"
  >
    <router-link
      v-for="tab in visibleTabs"
      :key="tab.slug"
      :to="settingsRoute(tab.slug)"
      role="tab"
      :aria-selected="tab.slug === active"
      class="flex flex-col"
    >
      <span
        class="px-1 py-2.5 text-[14px] font-medium leading-5"
        :class="
          tab.slug === active
            ? 'text-[var(--ct-accent)]'
            : 'text-[var(--ct-text-secondary)] hover:text-[var(--ct-text-primary)]'
        "
      >
        {{ __(tab.label) }}
      </span>
      <span
        class="h-0.5 w-full"
        :class="tab.slug === active ? 'bg-[var(--ct-accent)]' : ''"
      />
    </router-link>
  </div>
</template>

<script setup>
import { settingsRoute } from '@/composables/settingsNavigation'
import { computed } from 'vue'

// tabs: [{ slug, label (English, translated here), condition? }] (condition: same as the section's in
// settingsSections.js); active: slug of the section on screen
const props = defineProps({
  tabs: { type: Array, required: true },
  active: { type: String, required: true },
})

const visibleTabs = computed(() =>
  props.tabs.filter((tab) => !tab.condition || tab.condition()),
)
</script>
