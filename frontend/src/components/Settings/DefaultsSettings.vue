<template>
  <!-- Figma "Configurações · Empresa" (2323:14221), "Valores padrão" block:
       "Filtro" selects on the right of each row -->
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('System Defaults')">
      <template #description>
        {{
          __(
            'Set the currency, number, date and time formats used across your CRM.',
          )
        }}
      </template>
      <template #actions>
        <template v-if="isDirty">
          <Button
            v-if="isDirty"
            :label="__('Update')"
            variant="solid"
            :loading="settings.loading"
            @click="updateSettings"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <div v-if="settings.doc" class="flex flex-1 flex-col gap-6 overflow-y-auto">
      <SettingsRow>
        <template #label>
          {{ __('Currency') }}
        </template>
        <template #description>
          {{
            __(
              'Defines the default currency for all records, can be overridden at the field level',
            )
          }}
        </template>
        <Link v-model="settings.doc.currency" doctype="Currency">
          <template #target="{ togglePopover, isOpen }">
            <button type="button" class="ct-filter" @click="togglePopover()">
              <span class="truncate">{{ settings.doc.currency }}</span>
              <span
                class="size-4 shrink-0 text-[color:var(--ct-text-secondary)]"
                :class="isOpen ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                aria-hidden="true"
              />
            </button>
          </template>
        </Link>
      </SettingsRow>
      <SettingsRow>
        <template #label>
          {{ __('Currency Precision') }}
        </template>
        <template #description>
          {{ __('Number of decimal places used for all currency values') }}
        </template>
        <SettingsSelect
          v-model="settings.doc.currency_precision"
          :options="getOptions('currency_precision')"
          :placeholder="3"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Number Format') }}
        </template>
        <template #description>
          {{
            __(
              'Controls how numbers are displayed (e.g., commas, decimal separators)',
            )
          }}
        </template>
        <SettingsSelect
          v-model="settings.doc.number_format"
          :options="getOptions('number_format')"
        />
      </SettingsRow>
      <SettingsRow>
        <template #label>
          {{ __('Float Precision') }}
        </template>
        <template #description>
          {{ __('Number of decimal places for non-currency numeric fields') }}
        </template>
        <SettingsSelect
          v-model="settings.doc.float_precision"
          :options="getOptions('float_precision')"
          :placeholder="3"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Date Format') }}
        </template>
        <template #description>
          {{ __('Display format for dates across the system') }}
        </template>
        <SettingsSelect
          v-model="settings.doc.date_format"
          :options="getOptions('date_format')"
        />
      </SettingsRow>
      <SettingsRow>
        <template #label>
          {{ __('Time Format') }}
        </template>
        <template #description>
          {{ __('Select whether to display time with or without seconds') }}
        </template>
        <SettingsSelect
          v-model="settings.doc.time_format"
          :options="getOptions('time_format')"
        />
      </SettingsRow>
    </div>
  </div>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsSelect from '@/components/Settings/SettingsSelect.vue'
import Link from '@/components/Controls/Link.vue'
import { getMeta } from '@/stores/meta'
import { Button, toast, createDocumentResource } from 'frappe-ui'
import { computed } from 'vue'

const { getFields } = getMeta('System Settings')

const settings = createDocumentResource({
  doctype: 'System Settings',
  name: 'System Settings',
})

const isDirty = computed(() => {
  return JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc)
})

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Settings updated successfully'))
    },
    onError(error) {
      const message = error?.messages?.[0] || __('Failed to save settings')
      toast.error(message)
    },
  })
}

const fieldsMeta = computed(() => getFields() || [])

function getOptions(fieldname) {
  const field = fieldsMeta.value.find((f) => f.fieldname === fieldname)
  return field?.options || []
}
</script>
