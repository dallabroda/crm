<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Dashboard')">
      <template #description>
        {{ __('Choose how the dashboard forecasts deals and shows currency.') }}
      </template>
      <template #actions>
        <template v-if="settings.isDirty">
          <Button
            v-if="settings.isDirty"
            :label="__('Update')"
            variant="solid"
            :loading="settings.loading"
            @click="updateSettings"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <div class="flex flex-1 flex-col gap-6 overflow-y-auto">
      <SettingsRow>
        <template #label>
          {{ __('Enable Forecasting') }}
        </template>
        <template #description>
          {{
            __(
              'Makes "Expected Closure Date" and "Deal Value" mandatory for deal value forecasting',
            )
          }}
        </template>
        <Switch v-model="settings.doc.enable_forecasting" size="sm" />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Dashboard Currency') }}
        </template>
        <template #description>
          {{
            __(
              "Currency for dashboard cards and charts. Can't be changed once set.",
            )
          }}
        </template>
        <div v-if="settings.doc?.currency" class="text-base text-ink-gray-8">
          {{ settings.doc.currency }}
        </div>
        <Link
          v-else
          class="form-control flex-1 truncate w-40"
          :value="settings.doc?.currency"
          doctype="Currency"
          :placeholder="__('Select Currency')"
          placement="bottom-end"
          @change="(v) => setCurrency(v)"
        />
      </SettingsRow>
      <SettingsDivider />
      <SettingsRow>
        <template #label>
          {{ __('Exchange Rate Provider') }}
        </template>
        <template #description>
          {{ __('Configure the exchange rate provider for your CRM') }}
        </template>
        <FormControl
          v-model="settings.doc.service_provider"
          type="select"
          variant="outline"
          class="w-44"
          :options="[
            { label: 'Frankfurter', value: 'frankfurter.app' },
            {
              label: 'Fawaz Ahmed Exchange API',
              value: 'fawazahmed-exchange-api',
            },
            { label: 'Exchangerate Host', value: 'exchangerate.host' },
            { label: 'Exchangerate API', value: 'exchangerate-api' },
          ]"
          :placeholder="__('Select Provider')"
          :disabled="!settings.doc?.currency"
          @update:modelValue="() => (settings.doc.access_key = '')"
        />
      </SettingsRow>
      <div
        v-if="requiresAccessKey"
        class="h-px border-t mx-2 border-outline-elevation-2"
      />
      <div
        v-if="requiresAccessKey"
        class="flex items-center justify-between gap-8 p-3"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Access Key') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __('Access key for {0}. Required for fetching exchange rates.', [
                providerMeta.label,
              ])
            }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('You can get your access key from ') }}
            <a
              class="hover:underline text-ink-gray-7"
              :href="providerMeta.docsUrl"
              target="_blank"
            >
              {{ __(providerMeta.docsLabel) }}
            </a>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.access_key"
            type="text"
            class="w-44"
            :placeholder="__('Enter Access Key')"
            :disabled="!settings.doc?.currency"
          />
        </div>
      </div>
    </div>
    <div v-if="errorMessage" class="px-3">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { useBroadcast } from '@/composables/useBroadcast'
import { ErrorMessage, FormControl, Switch, toast } from 'frappe-ui'
import { useRoute } from 'vue-router'
import { ref, computed } from 'vue'

const route = useRoute()

const { _settings: settings } = getSettings()
const { $dialog } = globalStore()
const { send } = useBroadcast()

const errorMessage = ref('')

const PROVIDERS_REQUIRING_KEY = ['exchangerate.host', 'exchangerate-api']

const PROVIDER_META = {
  'exchangerate.host': {
    label: 'Exchangerate Host',
    docsUrl: 'https://exchangerate.host/#/docs/access_key',
    docsLabel: 'exchangerate.host',
  },
  'exchangerate-api': {
    label: 'Exchangerate API',
    docsUrl: 'https://www.exchangerate-api.com',
    docsLabel: 'exchangerate-api.com',
  },
}

const serviceProvider = computed(() => settings.doc?.service_provider)
const requiresAccessKey = computed(() =>
  PROVIDERS_REQUIRING_KEY.includes(serviceProvider.value),
)
const providerMeta = computed(() => PROVIDER_META[serviceProvider.value])

function updateSettings() {
  settings.save.submit(null, {
    validate: () => {
      errorMessage.value = ''
      if (!settings.doc?.currency) {
        errorMessage.value = __('Please select a currency before saving.')
        return errorMessage.value
      }
      if (requiresAccessKey.value && !settings.doc.access_key) {
        errorMessage.value = __('Please enter the {0} access key.', [
          providerMeta.value.label,
        ])
        return errorMessage.value
      }
    },
    onSuccess: () => {
      toast.success(__('Dashboard settings updated successfully'))

      if (route.name === 'Deal') {
        send('reload-deal-sections')
      }
    },
  })
}

function setCurrency(value) {
  $dialog({
    title: __('Set Currency'),
    message: __(
      'Are you sure you want to set the currency as {0}? This cannot be changed later.',
      [value],
    ),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Save'),
        variant: 'solid',
        onClick: ({ close }) => {
          settings.doc.currency = value
          settings.save.submit(null, {
            onSuccess: () => {
              toast.success(__('Currency set as {0} successfully', [value]))
              close()
            },
          })
        },
      },
    ],
  })
}
</script>
