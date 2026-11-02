<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('General Settings')">
      <template #description>
        {{ __('Configure general settings for your application.') }}
      </template>
    </SettingsPageHeader>

    <div class="flex flex-1 flex-col gap-6 overflow-y-auto">
      <SettingsRow>
        <template #label>
          {{ __('Update timestamp on new communication') }}
        </template>
        <template #description>
          {{
            __(
              'Update the modified timestamp on new email communication & comments for leads & deals',
            )
          }}
        </template>
        <Switch
          v-model="settings.doc.update_timestamp_on_new_communication"
          size="sm"
          @click.stop="toggle('update_timestamp_on_new_communication')"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Mark lead/deal as replied on response') }}
        </template>
        <template #description>
          {{
            __(
              'Automatically sets communication status to “Replied” for the lead or deal when a response is received. Applies only when SLA is enabled',
            )
          }}
        </template>
        <Switch
          v-model="settings.doc.auto_mark_replied_on_response"
          size="sm"
          @click.stop="toggle('auto_mark_replied_on_response')"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Reopen lead/deal on new communication') }}
        </template>
        <template #description>
          {{
            __(
              'Automatically sets communication status to “Open” for the lead or deal when a new communication is created. Applies only when SLA is enabled',
            )
          }}
        </template>
        <Switch
          v-model="settings.doc.auto_reopen_on_new_communication"
          size="sm"
          @click.stop="toggle('auto_reopen_on_new_communication')"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Timeline timestamp format') }}
        </template>
        <template #description>
          {{
            __(
              'Show timestamps in the activity timeline as relative time (5 mins ago) or an exact date & time',
            )
          }}
        </template>
        <FormControl
          v-model="settings.doc.crm_timeline_timestamp_format"
          type="select"
          variant="outline"
          class="w-40"
          :options="timestampFormatOptions"
          :placeholder="__('Relative')"
          @update:modelValue="save()"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Timeline sort order') }}
        </template>
        <template #description>
          {{
            __(
              'Order of activities, emails, comments and calls in the timeline',
            )
          }}
        </template>
        <FormControl
          v-model="settings.doc.crm_timeline_sort_order"
          type="select"
          variant="outline"
          class="w-40"
          :options="sortOrderOptions"
          :placeholder="__('Oldest First')"
          @update:modelValue="save()"
        />
      </SettingsRow>
    </div>
  </div>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import { getSettings } from '@/stores/settings'
import { FormControl, Switch, toast } from 'frappe-ui'

const { _settings: settings } = getSettings()

const timestampFormatOptions = [
  { label: __('Relative'), value: 'Relative' },
  { label: __('Exact'), value: 'Exact' },
]
const sortOrderOptions = [
  { label: __('Oldest First'), value: 'Oldest First' },
  { label: __('Newest First'), value: 'Newest First' },
]

function toggle(settingKey) {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(
        settings.doc[settingKey]
          ? __('Setting enabled successfully')
          : __('Setting disabled successfully'),
      )
    },
  })
}

function save() {
  settings.save.submit(null, {
    onSuccess: () => toast.success(__('Setting updated successfully')),
  })
}
</script>
