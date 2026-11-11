<template>
  <SettingsLayoutBase
    :title="__('ERP integration')"
    :description="
      __(
        'Direct connection with the ERP of your securitization company or factoring. The contract and the API credentials are your company\'s with the ERP; HubTech only does the technical integration.',
      )
    "
  >
    <template #header-actions>
      <div v-if="settings.doc && !settings.get.loading" class="flex gap-2">
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="settings.reload()"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="settings.save.loading"
          :disabled="!isDirty"
          @click="save"
        />
      </div>
    </template>
    <template #content>
      <!-- Figma "[HubTech CRM] · credtech#367 · Configurações › Crédito e cobrança › Integração com ERP"
           (2479:30217, review page 1979:3291): same rhythm as Cartório e localização -->
      <div v-if="settings.doc" class="flex flex-col gap-6 pb-12">
        <ErrorMessage :message="saveError" />

        <!-- ERP and credentials -->
        <section class="flex flex-col gap-6">
          <div class="flex items-start justify-between gap-4">
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('ERP') }}
              </div>
              <span class="text-base leading-5 text-ink-gray-6">
                {{
                  __(
                    'Choose the ERP and enter the API credentials it gave your company.',
                  )
                }}
              </span>
            </div>
            <Switch v-model="erpEnabled" />
          </div>
          <template v-if="settings.doc.erp_enabled">
            <div class="ct-field-48 grid grid-cols-2 gap-4">
              <FormControl
                v-model="settings.doc.erp_provider"
                type="select"
                :label="__('ERP')"
                :options="providerOptions"
                required
              />
              <template v-if="settings.doc.erp_provider === 'Smart Securities'">
                <FormControl
                  v-model="settings.doc.smart_base_url"
                  type="text"
                  :label="__('API address')"
                  placeholder="https://api.smartsecurities.com.br"
                />
                <FormControl
                  v-model="settings.doc.smart_client_id"
                  type="text"
                  :label="__('Client ID')"
                  autocomplete="off"
                  required
                />
                <Password
                  v-model="settings.doc.smart_client_secret"
                  :label="__('Client Secret')"
                  placeholder="************"
                  required
                />
              </template>
              <template v-else-if="settings.doc.erp_provider === 'WBA'">
                <FormControl
                  v-model="settings.doc.wba_base_url"
                  type="text"
                  :label="__('API address')"
                  placeholder="https://new-api.wba.com.br"
                />
                <FormControl
                  v-model="settings.doc.wba_tenant_id"
                  type="text"
                  :label="__('Tenant ID')"
                  autocomplete="off"
                  required
                />
                <FormControl
                  v-model="settings.doc.wba_username"
                  type="text"
                  :label="__('User')"
                  autocomplete="off"
                  required
                />
                <Password
                  v-model="settings.doc.wba_password"
                  :label="__('Password')"
                  placeholder="************"
                  required
                />
              </template>
            </div>
            <div>
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :label="__('Test connection')"
                icon-left="lucide-link"
                :loading="testing"
                :disabled="isDirty || !settings.originalDoc?.erp_enabled"
                @click="testConnection"
              />
            </div>
            <CtAlert v-if="connection" :type="connection.ok ? 'success' : 'error'">
              {{ connection.message }}
            </CtAlert>
          </template>
        </section>

        <template v-if="settings.doc.erp_enabled">
          <SettingsDivider />

          <!-- Cedente registration from the credit funnel (credtech#367, PR 3) -->
          <section class="flex flex-col gap-6">
            <div class="flex items-start justify-between gap-4">
              <div class="flex flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ __('Cedente registration (credit funnel)') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'Registers the card\'s company as a cedente in the ERP, with the Receita data (address, IBGE code and tax regime). Each send leaves a comment on the card with the manager. The ERP does not accept editing or deleting the registration by API.',
                    )
                  }}
                </span>
              </div>
              <Switch v-model="cedenteEnabled" />
            </div>
            <template v-if="settings.doc.cedente_send_enabled">
              <div class="ct-field-48 grid grid-cols-2 gap-4">
                <FormControl
                  v-model="settings.doc.cedente_trigger"
                  type="select"
                  :label="__('When to register')"
                  :options="triggerOptions"
                />
                <FormControl
                  v-model="settings.doc.cedente_pipeline"
                  type="select"
                  :label="__('Funnel')"
                  :options="pipelineOptions"
                  required
                />
                <FormControl
                  v-if="settings.doc.cedente_trigger === 'Card enters a stage'"
                  v-model="settings.doc.cedente_stage"
                  type="select"
                  :label="__('Stage')"
                  :options="stageOptions"
                  required
                />
                <FormControl
                  v-if="settings.doc.erp_provider === 'Smart Securities'"
                  v-model="settings.doc.default_manager"
                  type="select"
                  :label="__('Default manager')"
                  :options="managerOptions"
                />
              </div>
              <span class="text-p-sm text-ink-gray-5">
                {{
                  __(
                    'Manager: the card owner, when they are also a manager in the ERP; otherwise the default manager. Sector: automatic from the company\'s CNAE (e.g. CNAE 62 → IT services).',
                  )
                }}
              </span>
              <CtAlert v-if="lists.error" type="warning">
                {{ lists.error }}
              </CtAlert>
            </template>
          </section>

          <SettingsDivider />

          <!-- Overdue títulos from the ERP into the collection funnel (credtech#367, PR 4) -->
          <section
            v-if="settings.doc.erp_provider === 'Smart Securities'"
            class="flex flex-col gap-6"
          >
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('Overdue títulos in the collection funnel') }}
              </div>
              <span class="text-base leading-5 text-ink-gray-6">
                {{
                  __(
                    'Every day at 7:30 the overdue títulos of the ERP become cards in the collection funnel; settlements and repurchases close the títulos. The balance of ERP títulos is read-only on the card.',
                  )
                }}
              </span>
            </div>
            <FormControl
              v-model="dryRun"
              type="checkbox"
              :label="__('Simulation mode (nothing is saved)')"
              :description="
                __(
                  'On until you turn it off: each run only shows what it would create, update and close. Read the result before turning it off.',
                )
              "
            />
            <div class="ct-field-48 grid grid-cols-2 gap-4">
              <FormControl
                v-model="settings.doc.overdue_days"
                type="number"
                :label="__('Days overdue to become a card')"
              />
              <FormControl
                v-model="settings.doc.paid_lookback_days"
                type="number"
                :label="__('Check settlements of the last (days)')"
              />
            </div>
            <CtAlert v-if="settings.doc.last_sync_message" type="info">
              {{ settings.doc.last_sync_message }}
            </CtAlert>
            <div>
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :label="__('Sync now')"
                :loading="syncing"
                :disabled="isDirty || !settings.originalDoc?.erp_enabled"
                @click="syncNow"
              />
            </div>
          </section>

          <SettingsDivider
            v-if="settings.doc.erp_provider === 'Smart Securities'"
          />

          <!-- Field mapping: ready for the chosen ERP -->
          <section class="flex flex-col gap-6">
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('Field mapping') }}
              </div>
              <span class="text-base leading-5 text-ink-gray-6">
                {{
                  __(
                    'How each ERP field is filled with the CRM data. It comes ready for the chosen ERP; change it only if your portfolio uses something different.',
                  )
                }}
              </span>
            </div>
            <div
              v-if="mappingRows.length"
              class="ct-field-48 grid grid-cols-2 gap-4"
            >
              <FormControl
                v-for="row in mappingRows"
                :key="row.name || row.erp_field"
                :model-value="sourceLabel(row)"
                type="text"
                :label="__('{0} (ERP) ←', [__(row.label || row.erp_field)])"
                readonly
              />
            </div>
            <div>
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :label="__('Restore the default mapping')"
                :loading="resetting"
                :disabled="isDirty || !settings.originalDoc?.erp_provider"
                @click="resetMapping"
              />
            </div>
          </section>
        </template>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import '../fieldOutline.css'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import CtAlert from '@/components/CtAlert.vue'
import { useDocument } from '@/data/document'
import { pipelinesStore } from '@/stores/pipelines'
import { Badge, Button, ErrorMessage, FormControl, Switch, call, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

// WBA / Smart Securities integration (credtech#367), served by the cred_hub app.
// Admins only: the page holds the passwords of the company's ERP contract.
const DOCTYPE = 'Cred Hub ERP Settings'
const { document: settings } = useDocument(DOCTYPE, DOCTYPE)
const pipelineStore = pipelinesStore()
pipelineStore.ensureLoaded()

const saveError = ref('')
const testing = ref(false)
const syncing = ref(false)
const resetting = ref(false)
const connection = ref(null)
const lists = reactive({ managers: [], sectors: [], error: '' })

const FIELDS = [
  'erp_enabled',
  'erp_provider',
  'smart_base_url',
  'smart_client_id',
  'smart_client_secret',
  'wba_base_url',
  'wba_tenant_id',
  'wba_username',
  'wba_password',
  'cedente_send_enabled',
  'cedente_trigger',
  'cedente_pipeline',
  'cedente_stage',
  'default_manager',
  'sync_dry_run',
  'overdue_days',
  'paid_lookback_days',
]

function flag(field) {
  return computed({
    get: () => Boolean(settings.doc?.[field]),
    set: (value) => (settings.doc[field] = value ? 1 : 0),
  })
}
const erpEnabled = flag('erp_enabled')
const cedenteEnabled = flag('cedente_send_enabled')
const dryRun = flag('sync_dry_run')

const normalize = (value) =>
  typeof value === 'boolean' ? String(Number(value)) : String(value ?? '')

const isDirty = computed(() => {
  const doc = settings.doc
  const original = settings.originalDoc
  if (!doc || !original) return false
  return FIELDS.some((f) => normalize(doc[f]) !== normalize(original[f]))
})

const providerOptions = [
  { label: '', value: '' },
  { label: 'Smart Securities', value: 'Smart Securities' },
  { label: 'WBA', value: 'WBA' },
]
const triggerOptions = [
  { label: __('When the card enters a stage'), value: 'Card enters a stage' },
  { label: __('Manual only'), value: 'Manual only' },
]
const pipelineOptions = computed(() => [
  { label: '', value: '' },
  ...(pipelineStore.pipelines || []).map((p) => ({
    label: __(p.pipeline_name || p.name),
    value: p.name,
  })),
])
const stageOptions = computed(() => {
  const pipeline = settings.doc?.cedente_pipeline
    ? pipelineStore.getPipeline(settings.doc.cedente_pipeline)
    : null
  return [
    { label: '', value: '' },
    ...(pipeline?.stages || []).map((s) => ({
      label: __(s.deal_status),
      value: s.name,
    })),
  ]
})
// The manager is chosen by name from the ERP's own list: no id is ever typed in the CRM
const managerOptions = computed(() => {
  const names = [...lists.managers]
  const current = settings.doc?.default_manager
  if (current && !names.includes(current)) names.unshift(current)
  return [{ label: '', value: '' }, ...names.map((n) => ({ label: n, value: n }))]
})

// A stage of another funnel is not valid: clear it when the funnel changes
watch(
  () => settings.doc?.cedente_pipeline,
  (pipeline, previous) => {
    if (previous !== undefined && pipeline !== previous && settings.doc) {
      settings.doc.cedente_stage = ''
    }
  },
)

async function loadLists() {
  if (!settings.originalDoc?.erp_enabled) return
  try {
    const data = await call('cred_hub.erp.settings.erp_lists')
    lists.managers = data.managers || []
    lists.sectors = data.sectors || []
    lists.error = data.error || ''
  } catch (err) {
    lists.error = err.messages?.[0] || err.message
  }
}
watch(
  () => settings.originalDoc?.erp_provider,
  () => loadLists(),
  { immediate: true },
)

const mappingRows = computed(() => settings.doc?.cedente_field_map || [])
const SOURCE_LABELS = {
  organization: __('Company'),
  contact: __('Contact'),
  address: __('Address'),
  deal: __('Card'),
  credit: __('Credit committee'),
}
function sourceLabel(row) {
  if (row.source === 'auto') return __('Automatic (from the ERP lists)')
  if (row.source === 'today') return __('Date of the registration')
  if (!row.source) return row.default_value || '-'
  const first = row.source.split('|')[0]
  const [entity, field] = first.split('.')
  return `${SOURCE_LABELS[entity] || entity} › ${field}`
}

function save() {
  saveError.value = ''
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      connection.value = null
      toast.success(__('ERP settings saved'))
    },
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

async function testConnection() {
  testing.value = true
  try {
    connection.value = await call('cred_hub.erp.settings.test_connection')
    if (connection.value.ok) loadLists()
  } catch (err) {
    connection.value = { ok: false, message: err.messages?.[0] || err.message }
  } finally {
    testing.value = false
  }
}

async function syncNow() {
  syncing.value = true
  try {
    const { ok, message } = await call('cred_hub.erp.sync.sync_now')
    ok ? toast.success(message) : toast.error(message)
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  } finally {
    syncing.value = false
  }
}

async function resetMapping() {
  resetting.value = true
  try {
    await call('cred_hub.erp.settings.reset_field_map')
    settings.reload()
    toast.success(__('Default mapping restored'))
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  } finally {
    resetting.value = false
  }
}
</script>
