<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Home Actions')">
      <template #description>
        {{ __('Configure actions that appear on the home dropdown.') }}
      </template>
      <template #actions>
        <template v-if="document.isDirty">
          <Button
            v-if="document.isDirty"
            :label="__('Update')"
            variant="solid"
            :loading="document.loading"
            @click="updateSettings"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <!-- Fields: Figma "Configurações · Ações da página inicial" (881:2) table -->
    <div class="ct-home-actions flex flex-1 flex-col overflow-y-auto">
      <Grid
        v-model="document.doc.dropdown_items"
        doctype="CRM Dropdown Item"
        parentDoctype="FCRM Settings"
        parentFieldname="dropdown_items"
      />
    </div>
    <div v-if="errorMessage">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import Grid from '@/components/Controls/Grid.vue'
import { ErrorMessage } from 'frappe-ui'
import { showSettings } from '@/composables/settings'
import { useDocument } from '@/data/document'
import { ref, provide } from 'vue'

const { document, triggerOnChange } = useDocument(
  'FCRM Settings',
  'FCRM Settings',
)

provide('triggerOnChange', triggerOnChange)

const errorMessage = ref('')

function updateSettings() {
  document.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>

<style scoped>
/* Figma "Tabela": 8px radius and soft border, 40px gray header with 12/500
   labels, 56px white rows split only by horizontal lines */
.ct-home-actions :deep(.rounded-4.border) {
  border-radius: var(--ct-radius-md);
  border-color: var(--ct-border-soft);
}
.ct-home-actions :deep(.grid-header) {
  height: 40px;
  border-bottom: 1px solid var(--ct-border-soft);
  background: var(--ct-bg-soft);
  font-size: 12px;
  font-weight: 500;
  color: var(--ct-text-secondary);
}
.ct-home-actions :deep(.border-r) {
  border-right-color: transparent;
}
.ct-home-actions :deep(.grid-row) {
  padding-block: 9px;
  border-color: var(--ct-border-soft);
}
.ct-home-actions :deep(.grid-row input),
.ct-home-actions :deep(.grid-row .text-sm) {
  font-size: 14px;
}
</style>
