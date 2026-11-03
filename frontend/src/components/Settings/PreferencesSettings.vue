<template>
  <SettingsLayoutBase
    v-if="user.doc"
    :title="__('Preferences')"
    :description="
      __(
        'Choose how you want to use the application by setting your preferences.',
      )
    "
  >
    <template #content>
      <!-- Figma "Configurações · Preferências" (825:2): "Aparência" with the
           theme cards, divider, "Idioma e horário" rows with Filtro selects -->
      <div class="flex flex-col gap-6">
        <div class="text-lg font-medium leading-6 text-ink-gray-9">
          {{ __('Appearance') }}
        </div>
        <div class="flex flex-col gap-3">
          <SettingsRow
            :label="__('Theme')"
            :description="__('Switch between light, dark, or system theme')"
          />
          <ThemeSwitcher
            :logo="brand.logo || CRMLogo"
            :name="brand.name || 'HubTech CRM'"
          />
        </div>
        <SettingsDivider />
        <div class="flex items-center justify-between">
          <div class="flex h-7 items-center gap-2">
            <div class="text-lg font-medium leading-6 text-ink-gray-9">
              {{ __('Language & Time') }}
            </div>
            <Badge
              v-if="isDirty"
              :variant="'subtle'"
              :theme="'amber'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
          <Button
            v-if="isDirty"
            variant="solid"
            :label="__('Save')"
            :loading="user.save.loading"
            @click="save()"
          />
        </div>
        <SettingsRow
          :label="__('Language')"
          :description="__('Change language of the application.')"
        >
          <Link
            v-model="user.doc.language"
            doctype="Language"
            variant="outline"
            class="w-44"
          />
        </SettingsRow>
        <SettingsRow
          :label="__('Timezone')"
          :description="__('Change timezone of the application.')"
        >
          <Combobox
            v-model="user.doc.time_zone"
            variant="outline"
            class="w-44"
            :options="getTimezoneOptions()"
          />
        </SettingsRow>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import ThemeSwitcher from '@/components/Settings/ThemeSwitcher.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import Link from '@/components/Controls/Link.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { getSettings } from '@/stores/settings'
import {
  Combobox,
  Badge,
  toast,
  createResource,
  createDocumentResource,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'

const refreshRequired = ref(false)

const { user: sessionUser } = inject('session')

const { brand } = getSettings()
const user = createDocumentResource({ doctype: 'User', name: sessionUser })

function save() {
  refreshRequired.value =
    user.doc.language !== user.originalDoc?.language ||
    user.doc.time_zone !== user.originalDoc?.time_zone

  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Preferences updated successfully'))
      if (refreshRequired.value) {
        window.location.reload()
      }
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  })
}

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc)
})

const timeZones = createResource({
  url: 'frappe.core.doctype.user.user.get_timezones',
  cache: 'TimeZones',
  auto: true,
})

function getTimezoneOptions() {
  return timeZones.data?.timezones.map((tz) => ({ label: tz, value: tz })) || []
}

useKeyboardShortcuts({
  ignoreTyping: false,
  shortcuts: [
    {
      match: (e) => (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's',
      action: () => {
        if (isDirty.value) {
          save()
        }
      },
    },
  ],
})
</script>
