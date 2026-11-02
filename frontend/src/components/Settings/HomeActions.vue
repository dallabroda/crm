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

    <!-- Fields -->
    <div class="flex flex-1 flex-col overflow-y-auto">
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
