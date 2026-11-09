<template>
  <!-- Figma "Barra superior" (1185:15520): the saved-view switch is a
       "Filtro" (white, grey border, 32px, no icon) right before "Criar". -->
  <Dropdown
    v-if="viewControls && viewControls.viewsDropdownOptions"
    align="end"
    :options="viewControls.viewsDropdownOptions"
  >
    <template #default="{ open }">
      <button type="button" class="ct-filter">
        <span class="truncate">{{ __(viewControls.currentView?.label) }}</span>
        <span
          class="size-4 shrink-0"
          :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
          aria-hidden="true"
        />
      </button>
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
</template>
<script setup>
import { Dropdown } from 'frappe-ui'

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
