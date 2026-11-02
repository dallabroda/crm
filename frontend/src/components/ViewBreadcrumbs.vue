<template>
  <!-- Figma "Barra superior": page title 20 Semi Bold; the saved-view switch
       is a "Filtro" (outline, 32px) next to it. -->
  <div class="flex min-w-0 items-center gap-3">
    <router-link
      :to="{ name: routeName }"
      class="truncate rounded-[var(--ct-radius-sm)] text-[20px] font-semibold leading-7 text-ink-gray-9 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
    >
      {{ __(title || routeName) }}
    </router-link>
    <Dropdown
      v-if="viewControls && viewControls.viewsDropdownOptions"
      :options="viewControls.viewsDropdownOptions"
    >
      <template #default="{ open }">
        <Button
          variant="outline"
          class="text-nowrap"
          :label="__(viewControls.currentView?.label)"
          :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        >
          <template #prefix>
            <Icon :icon="viewControls.currentView?.icon" class="h-4" />
          </template>
        </Button>
      </template>
      <template #item-suffix="{ item, close, selected }">
        <div v-if="item.name" class="flex flex-row-reverse gap-2 items-center">
          <Dropdown
            side="right"
            :offset="15"
            :options="viewControls.viewActions(item, close)"
          >
            <template #default>
              <Button
                variant="ghost"
                class="view-action-btn !size-5 opacity-0"
                icon="lucide-more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
          <span
            v-if="selected"
            class="lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
          />
          <span v-if="item.isDefault" class="text-sm text-ink-gray-5">
            {{ __('Default') }}
          </span>
        </div>
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import { Dropdown } from 'frappe-ui'

defineProps({
  routeName: { type: String, required: true },
  // shown instead of the route name (a funnel shows its own name), translated
  // with __() like the sidebar does, so "Sales" reads "Vendas" in both places
  title: { type: String, default: '' },
})

const viewControls = defineModel({ type: Object, default: () => ({}) })
</script>

<style scoped>
/* frappe-ui's Menu rewrite dropped the `group` class from item rows, so
   reveal the view actions on row hover/highlight instead of `group-hover`. */
[data-slot='item']:hover .view-action-btn,
[data-slot='item'][data-highlighted] .view-action-btn {
  opacity: 1;
}
</style>
