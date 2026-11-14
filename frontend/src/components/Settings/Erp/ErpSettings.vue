<template>
  <SettingsLayoutBase
    :title="__('Crédito e cobrança')"
    :description="
      __(
        'Direct connection with the ERP of your securitization company or factoring. The contract and the API credentials are your company\'s with the ERP; HubTech only does the technical integration.',
      )
    "
  >
    <!-- the tabs of "Crédito e cobrança" (no sub-items in the menu) -->
    <template #header-top>
      <CreditTabs active="page:erp-integration" />
    </template>
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
          <div class="flex items-center justify-between gap-6">
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
            <Switch v-model="erpEnabled" size="md" />
          </div>
          <template v-if="settings.doc.erp_enabled">
            <div class="ct-field-48 grid grid-cols-2 gap-4">
              <FormControl
                v-model="settings.doc.erp_provider"
                type="select"
                :placeholder="__('Select')"
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
                size="lg"
                class="ct-btn-accent-text ct-erp-icon-24"
                :label="__('Test connection')"
                icon-left="lucide-link-2"
                :loading="testing"
                :disabled="isDirty || !settings.originalDoc?.erp_enabled"
                @click="testConnection"
              />
            </div>
            <CtAlert
              v-if="connection"
              :type="connection.ok ? 'success' : 'error'"
            >
              {{ connection.message }}
            </CtAlert>
          </template>
        </section>

        <template v-if="settings.doc.erp_enabled">
          <SettingsDivider />

          <!-- Cedente registration from the credit funnel (credtech#367, PR 3) -->
          <section class="flex flex-col gap-6">
            <div class="flex items-center justify-between gap-6">
              <div class="flex flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{ __('Cedente registration (credit funnel)') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      "Registers the card's company as a cedente in the ERP, with the Receita data (address, IBGE code and tax regime). Each send leaves a comment on the card with the manager. The ERP does not accept editing or deleting the registration by API.",
                    )
                  }}
                </span>
              </div>
              <Switch v-model="cedenteEnabled" size="md" />
            </div>
            <template v-if="settings.doc.cedente_send_enabled">
              <div class="ct-field-48 grid grid-cols-2 gap-4">
                <FormControl
                  v-model="settings.doc.cedente_trigger"
                  type="select"
                  :placeholder="__('Select')"
                  :label="__('When to register')"
                  :options="triggerOptions"
                />
                <FormControl
                  v-model="settings.doc.cedente_pipeline"
                  type="select"
                  :placeholder="__('Select')"
                  :label="__('Funnel')"
                  :options="pipelineOptions"
                  required
                />
                <FormControl
                  v-if="settings.doc.cedente_trigger === 'Card enters a stage'"
                  v-model="settings.doc.cedente_stage"
                  type="select"
                  :placeholder="__('Select')"
                  :label="__('Stage')"
                  :options="stageOptions"
                  required
                />
                <FormControl
                  v-if="settings.doc.erp_provider === 'Smart Securities'"
                  v-model="settings.doc.default_manager"
                  type="select"
                  :placeholder="__('Select')"
                  :label="__('Default manager')"
                  :options="managerOptions"
                />
              </div>
              <span class="text-[12px] leading-4 text-ink-gray-6">
                {{
                  __(
                    "Manager: the card owner, when they are also a manager in the ERP; otherwise the default manager. Sector: automatic from the company's CNAE (e.g. CNAE 62 → IT services).",
                  )
                }}
              </span>
              <CtAlert v-if="lists.error" type="warning">
                {{ lists.error }}
              </CtAlert>
            </template>

            <p
              v-if="
                settings.doc.cedente_send_enabled && mappingLoading && !mapping
              "
              class="text-base leading-5 text-ink-gray-6"
            >
              {{ __('Loading the field mapping…') }}
            </p>

            <!-- De-para (Ida: CRM → ERP) — collapsed by default inside Cedente registration -->
            <div
              v-if="
                mapping &&
                (settings.doc.cedente_send_enabled ||
                  (cedenteValidationTriggered &&
                    missingRequiredCedente.length > 0))
              "
              ref="cedenteAccordionEl"
              class="rounded-[8px] border bg-[var(--ct-bg-page)]"
              :class="
                cedenteValidationTriggered && missingRequiredCedente.length > 0
                  ? 'border-[var(--ct-danger)]'
                  : 'border-[var(--ct-border)]'
              "
            >
              <button
                type="button"
                class="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left transition-colors hover:bg-[var(--ct-bg-soft)]"
                :class="
                  openSections.cedente ? 'rounded-t-[8px]' : 'rounded-[8px]'
                "
                :aria-expanded="openSections.cedente"
                @click="openSections.cedente = !openSections.cedente"
              >
                <span class="flex min-w-0 items-center gap-2.5">
                  <span
                    class="size-4 shrink-0 text-[var(--ct-text-secondary)]"
                    :class="
                      openSections.cedente
                        ? 'lucide-chevron-down'
                        : 'lucide-chevron-right'
                    "
                    aria-hidden="true"
                  />
                  <span
                    class="truncate text-[14px] font-semibold leading-5 text-[var(--ct-text-primary)]"
                  >
                    {{
                      __('Field mapping · Cedente registration (CRM → ERP)')
                    }}
                  </span>
                </span>
                <span class="flex shrink-0 items-center gap-2">
                  <span
                    v-if="
                      cedenteValidationTriggered &&
                      missingRequiredCedente.length > 0
                    "
                    class="inline-flex items-center rounded-full bg-[var(--ct-danger-soft)] px-2.5 py-1 text-[12px] font-medium leading-4 text-[var(--ct-danger)]"
                  >
                    {{
                      missingRequiredCedente.length === 1
                        ? __('1 required pending')
                        : __('{0} required pending', [
                            missingRequiredCedente.length,
                          ])
                    }}
                  </span>
                  <span
                    class="inline-flex items-center rounded-full border border-[var(--ct-border-soft)] bg-[var(--ct-bg-soft)] px-2.5 py-1 text-[12px] font-medium leading-4 text-[var(--ct-text-secondary)]"
                  >
                    {{ activeFieldsLabel(activeCedenteCount) }}
                  </span>
                </span>
              </button>

              <div
                v-if="openSections.cedente"
                class="flex flex-col gap-4 border-t border-[var(--ct-border-soft)] p-4"
              >
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'Each field of the cedente registration in the ERP and where it comes from in the CRM: a field, a fixed value, a name of the ERP list or do not send.',
                    )
                  }}
                  {{ __('* required by the ERP.') }}
                </span>
                <div class="ct-field-48 grid grid-cols-2 gap-4">
                  <div
                    v-for="field in shownCedenteFields"
                    :key="field.erp_field"
                    class="flex flex-col gap-2"
                  >
                    <FormControl
                      v-if="field.kind === 'auto'"
                      type="text"
                      :label="fieldLabel(field)"
                      :model-value="__('Automatic (from the ERP lists)')"
                      readonly
                    />
                    <FormControl
                      v-else-if="field.kind === 'list'"
                      type="select"
                      :label="fieldLabel(field)"
                      :options="listOptions(field)"
                      :model-value="
                        cedenteRow(field.erp_field)?.default_value || ''
                      "
                      @update:model-value="(v) => pickList(field, v)"
                    />
                    <template v-else>
                      <FormControl
                        type="select"
                        :label="fieldLabel(field)"
                        :options="sourceOptions(field)"
                        :model-value="sourceValue(field)"
                        @update:model-value="(v) => pickSource(field, v)"
                      />
                      <FormControl
                        v-if="sourceValue(field) === FIXED"
                        type="text"
                        :placeholder="__('Fixed value')"
                        :model-value="
                          cedenteRow(field.erp_field)?.default_value || ''
                        "
                        @update:model-value="
                          (v) => (cedenteRow(field.erp_field).default_value = v)
                        "
                      />
                    </template>
                  </div>
                </div>
                <div
                  v-if="hiddenCedenteOptions.length > 1"
                  class="ct-field-48 grid grid-cols-2 gap-4"
                >
                  <FormControl
                    type="select"
                    :options="hiddenCedenteOptions"
                    model-value=""
                    @update:model-value="
                      (v) => v && showMore.add('cedente:' + v)
                    "
                  />
                </div>
              </div>
            </div>

            <div
              v-if="
                mapping &&
                settings.doc.cedente_send_enabled &&
                settings.doc.erp_provider !== 'Smart Securities'
              "
            >
              <Button
                variant="outline"
                size="lg"
                class="ct-btn-accent-text"
                :label="__('Restore the default mapping')"
                :loading="resetting"
                :disabled="isDirty || !settings.originalDoc?.erp_provider"
                @click="resetMapping"
              />
            </div>
          </section>

          <SettingsDivider
            v-if="settings.doc.erp_provider === 'Smart Securities'"
          />

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
                    'Every day at 8:45 the overdue títulos of the ERP become cards in the collection funnel; settlements and repurchases close the títulos. The balance of ERP títulos is read-only on the card.',
                  )
                }}
              </span>
            </div>
            <!-- Figma "Opção": checkbox 20px, help 12/16 under the label -->
            <div class="ct-erp-option flex flex-col gap-0.5">
              <FormControl
                v-model="dryRun"
                type="checkbox"
                :label="__('Simulation mode (nothing is saved)')"
              />
              <p class="pl-[26px] text-[12px] leading-4 text-ink-gray-6">
                {{
                  __(
                    'On until you turn it off: each run only shows what it would create, update and close. Read the result before turning it off.',
                  )
                }}
              </p>
            </div>
            <CtAlert v-if="settings.doc.last_sync_message" type="info">
              {{ settings.doc.last_sync_message }}
            </CtAlert>
            <details
              v-if="settings.doc.last_sync_report"
              class="rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] px-3.5 py-2.5"
            >
              <summary
                class="cursor-pointer text-p-base font-medium text-ink-gray-8"
              >
                {{ __('Simulation report: what the sync would do') }}
              </summary>
              <pre
                class="mt-2 max-h-80 overflow-auto whitespace-pre-wrap text-p-sm text-ink-gray-7"
                >{{ settings.doc.last_sync_report }}</pre
              >
            </details>
            <!-- Approved Figma: "Sync now" (40px) in the same row as the two
                 fields, bottom-aligned; the fields fill the rest of the row -->
            <div class="flex items-end gap-4">
              <div class="ct-field-48 flex min-w-0 flex-1 gap-4">
                <div class="min-w-0 flex-1">
                  <FormControl
                    v-model="settings.doc.overdue_days"
                    type="number"
                    :label="__('Days overdue to become a card')"
                  />
                </div>
                <div class="min-w-0 flex-1">
                  <FormControl
                    v-model="settings.doc.paid_lookback_days"
                    type="number"
                    :label="__('Check settlements of the last (days)')"
                  />
                </div>
              </div>
              <Button
                variant="outline"
                size="lg"
                class="ct-btn-accent-text"
                :label="__('Sync now')"
                :loading="syncing"
                :disabled="isDirty || !settings.originalDoc?.erp_enabled"
                @click="syncNow"
              />
            </div>

            <p
              v-if="mappingLoading && !mapping"
              class="text-base leading-5 text-ink-gray-6"
            >
              {{ __('Loading the field mapping…') }}
            </p>

            <!-- De-para (Volta: ERP → CRM) — collapsed accordions inside Collection section -->
            <div v-if="mapping" class="flex flex-col gap-3">
              <div class="flex flex-col gap-1">
                <div
                  class="text-[16px] font-semibold leading-6 text-ink-gray-9"
                >
                  {{ __('Field mapping (ERP → CRM)') }}
                </div>
                <span class="text-base leading-5 text-ink-gray-6">
                  {{
                    __(
                      'You choose which ERP columns to bring on sync. Click a group to expand and edit.',
                    )
                  }}
                </span>
              </div>

              <div
                v-for="part in importParts"
                :key="part.table"
                class="rounded-[8px] border border-[var(--ct-border)] bg-[var(--ct-bg-page)]"
              >
                <button
                  type="button"
                  class="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left transition-colors hover:bg-[var(--ct-bg-soft)]"
                  :class="
                    openSections[part.table] ? 'rounded-t-[8px]' : 'rounded-[8px]'
                  "
                  :aria-expanded="openSections[part.table]"
                  @click="openSections[part.table] = !openSections[part.table]"
                >
                  <span class="flex min-w-0 items-center gap-2.5">
                    <span
                      class="size-4 shrink-0 text-[var(--ct-text-secondary)]"
                      :class="
                        openSections[part.table]
                          ? 'lucide-chevron-down'
                          : 'lucide-chevron-right'
                      "
                      aria-hidden="true"
                    />
                    <span
                      class="truncate text-[14px] font-semibold leading-5 text-[var(--ct-text-primary)]"
                    >
                      {{ part.title }}
                    </span>
                  </span>
                  <span
                    class="inline-flex shrink-0 items-center rounded-full border border-[var(--ct-border-soft)] bg-[var(--ct-bg-soft)] px-2.5 py-1 text-[12px] font-medium leading-4 text-[var(--ct-text-secondary)]"
                  >
                    {{ activeFieldsLabel(activeImportCount(part)) }}
                  </span>
                </button>

                <div
                  v-if="openSections[part.table]"
                  class="flex flex-col gap-4 border-t border-[var(--ct-border-soft)] p-4"
                >
                  <span class="text-base leading-5 text-ink-gray-6">{{
                    part.hint
                  }}</span>
                  <div class="ct-field-48 grid grid-cols-2 gap-4">
                    <template
                      v-for="column in shownColumns(part)"
                      :key="column"
                    >
                      <FormControl
                        v-if="part.options.fixed[column]"
                        type="text"
                        :label="__('{0} (ERP) →', [column])"
                        :model-value="__('Read automatically')"
                        readonly
                      />
                      <FormControl
                        v-else
                        type="select"
                        :label="__('{0} (ERP) →', [column])"
                        :options="importOptions(part)"
                        :model-value="importValue(part.table, column)"
                        @update:model-value="
                          (v) => pickImport(part.table, column, v)
                        "
                      />
                    </template>
                  </div>
                  <div
                    v-if="hiddenColumnOptions(part).length > 1"
                    class="ct-field-48 grid grid-cols-2 gap-4"
                  >
                    <FormControl
                      type="select"
                      :options="hiddenColumnOptions(part)"
                      model-value=""
                      @update:model-value="
                        (v) => v && showMore.add(part.table + ':' + v)
                      "
                    />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <Button
                variant="outline"
                size="lg"
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

  <Dialog
    v-model:open="newFieldModal.show"
    :size="'md'"
    :title="__('Criar novo campo no CRM')"
  >
    <template #default>
      <div class="flex flex-col gap-4 py-2">
        <p class="text-base text-ink-gray-6">
          {{
            __(
              'Crie um campo no CRM para receber os dados da coluna {0} do ERP.',
              [newFieldModal.column],
            )
          }}
        </p>
        <FormControl
          v-model="newFieldModal.label"
          type="text"
          :label="__('Nome do campo no CRM *')"
          :placeholder="__('Ex.: Situação ERP')"
          required
        />
        <FormControl
          v-model="newFieldModal.fieldtype"
          type="select"
          :label="__('Tipo de dado *')"
          :options="fieldTypeOptions"
        />
        <FormControl
          v-if="newFieldModal.table !== 'title_field_map'"
          v-model="newFieldModal.entity"
          type="select"
          :label="__('Vincular a *')"
          :options="[
            { label: __('Empresa (Organização)'), value: 'organization' },
            { label: __('Contato (Pessoa física / sócio)'), value: 'contact' },
          ]"
        />
        <div class="mt-2 flex justify-end gap-2">
          <Button
            :label="__('Cancelar')"
            variant="subtle"
            @click="newFieldModal.show = false"
          />
          <Button
            :label="__('Criar e Mapear')"
            variant="solid"
            class="ct-btn-primary"
            :loading="newFieldModal.loading"
            :disabled="!newFieldModal.label?.trim()"
            @click="submitCreateCustomField"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CreditTabs from '@/components/Settings/CreditBureaus/CreditTabs.vue'
import '../fieldOutline.css'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import CtAlert from '@/components/CtAlert.vue'
import { useDocument } from '@/data/document'
import { createDialog } from '@/utils/dialogs'
import { pipelinesStore } from '@/stores/pipelines'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Switch,
  call,
  toast,
} from 'frappe-ui'
import { computed, nextTick, reactive, ref, watch } from 'vue'

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
  return (
    FIELDS.some((f) => normalize(doc[f]) !== normalize(original[f])) ||
    mapShape(doc) !== mapShape(original)
  )
})

const providerOptions = [
  { label: __('Select'), value: '' },
  { label: 'Smart Securities', value: 'Smart Securities' },
  { label: 'WBA', value: 'WBA' },
]
const triggerOptions = [
  { label: __('When the card enters a stage'), value: 'Card enters a stage' },
  { label: __('Manual only'), value: 'Manual only' },
]
const pipelineOptions = computed(() => [
  { label: __('Select'), value: '' },
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
    { label: __('Select'), value: '' },
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
  return [
    { label: __('Select'), value: '' },
    ...names.map((n) => ({ label: n, value: n })),
  ]
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

// De-para (credtech#367): the options come from the server (every ERP field and column, every CRM field)
const mapping = ref(null)
const mappingLoading = ref(false)
const mappingLists = ref({})
// Fields and columns the admin added on the screen (the rest stays hidden until chosen)
const showMore = reactive(new Set())
// All de-para sections start collapsed by default; required-field errors open them automatically on save
const openSections = reactive({
  cedente: false,
  title_field_map: false,
  sacado_field_map: false,
  cedente_registry_map: false,
})
const cedenteAccordionEl = ref(null)
const cedenteValidationTriggered = ref(false)
const FIXED = '__fixed'
const LIST_SOURCE = 'erp_list'

async function loadMapping() {
  if (!settings.originalDoc?.erp_provider) return (mapping.value = null)
  mappingLoading.value = true
  try {
    mapping.value = await call('cred_hub.erp.settings.mapping_options')
  } catch (err) {
    mapping.value = null
    toast.error(err.messages?.[0] || err.message)
  } finally {
    mappingLoading.value = false
  }
  // The names of the ERP lists call the ERP (slow the first time): they come apart, the screen does not wait
  call('cred_hub.erp.settings.mapping_lists')
    .then((lists) => (mappingLists.value = lists || {}))
    .catch(() => (mappingLists.value = {}))
}
watch(() => settings.originalDoc?.erp_provider, loadMapping, {
  immediate: true,
})

// As in the Figma: "Razão social * (ERP) ←" (the arrow shows the direction, CRM → ERP)
const fieldLabel = (field) =>
  __('{0} (ERP) ←', [__(field.label) + (field.required === 'yes' ? ' *' : '')])

function cedenteRow(erpField) {
  return (settings.doc?.cedente_field_map || []).find(
    (r) => r.erp_field === erpField,
  )
}
function ensureCedenteRow(field) {
  let row = cedenteRow(field.erp_field)
  if (!row) {
    row = {
      erp_field: field.erp_field,
      label: field.label,
      source: '',
      default_value: '',
    }
    settings.doc.cedente_field_map = [
      ...(settings.doc.cedente_field_map || []),
      row,
    ]
    row = cedenteRow(field.erp_field)
  }
  return row
}
function dropCedenteRow(erpField) {
  settings.doc.cedente_field_map = settings.doc.cedente_field_map.filter(
    (r) => r.erp_field !== erpField,
  )
}

function sourceValue(field) {
  const row = cedenteRow(field.erp_field)
  if (!row) return ''
  if (row.source) return row.source
  return row.default_value ? FIXED : ''
}
function sourceOptions(field) {
  const sources = mapping.value?.cedente.sources || []
  const options = [
    {
      label: field.required === 'yes' ? __('Select') : __('Do not send'),
      value: '',
    },
    { label: __('Fixed value'), value: FIXED },
    ...sources,
  ]
  // "a|b": the second CRM field is used when the first is empty
  const current = cedenteRow(field.erp_field)?.source
  if (current && !sources.some((o) => o.value === current)) {
    const names = current
      .split('|')
      .map((s) => sources.find((o) => o.value === s)?.label || s)
    options.splice(2, 0, {
      label: names.join(' ' + __('or, if empty,') + ' '),
      value: current,
    })
  }
  return options
}
function pickSource(field, value) {
  if (!value) return dropCedenteRow(field.erp_field)
  const row = ensureCedenteRow(field)
  if (value === FIXED) {
    row.source = ''
    row.default_value = row.default_value || ''
  } else {
    row.source = value
    row.default_value = ''
  }
}

function listOptions(field) {
  const names = [...(mappingLists.value?.[field.resource] || [])]
  const current = cedenteRow(field.erp_field)?.default_value
  if (current && !names.includes(current)) names.unshift(current)
  return [
    { label: __('Do not send'), value: '' },
    ...names.map((n) => ({ label: n, value: n })),
  ]
}
function pickList(field, value) {
  if (!value) return dropCedenteRow(field.erp_field)
  const row = ensureCedenteRow(field)
  row.source = LIST_SOURCE
  row.default_value = value
}

const importParts = computed(() =>
  mapping.value
    ? [
        {
          table: 'title_field_map',
          options: mapping.value.title,
          title: __('Títulos (ERP → CRM)'),
          hint: __(
            'Each column of the ERP títulos goes to the título field you choose, on every sync. The protest species is always picked by the operator.',
          ),
          none: __('Do not bring'),
        },
        {
          table: 'sacado_field_map',
          options: mapping.value.sacado,
          title: __('Sacados (ERP → CRM)'),
          hint: __(
            'Read once, when the sync creates the sacado: the columns you choose fill its company or person and its contact. A sacado that already exists is not read again; the CNPJ data comes from the automatic enrichment.',
          ),
          none: __('Do not bring'),
        },
        {
          table: 'cedente_registry_map',
          options: mapping.value.cedente_registry,
          title: __('Cedentes (ERP → CRM)'),
          hint: __(
            'Read once, when the sync creates the cedente: the columns you choose fill its company and its contact. A cedente that already exists is not read again; the CNPJ data comes from the automatic enrichment.',
          ),
          none: __('Do not bring'),
        },
      ]
    : [],
)
const columnKey = (name) =>
  String(name || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((w) => w && w !== 'de')
    .join('')
// Only what the company uses is shown: required, automatic, already chosen or added now
const shownCedenteFields = computed(() => {
  const shown = (mapping.value?.cedente.fields || []).filter(
    (f) =>
      f.required === 'yes' ||
      f.kind === 'auto' ||
      cedenteRow(f.erp_field) ||
      showMore.has('cedente:' + f.erp_field),
  )
  return [
    ...shown.filter((f) => f.kind !== 'auto'),
    ...shown.filter((f) => f.kind === 'auto'),
  ]
})
const hiddenCedenteOptions = computed(() => [
  { label: __('+ Add an ERP field'), value: '' },
  ...(mapping.value?.cedente.fields || [])
    .filter((f) => !shownCedenteFields.value.includes(f))
    .map((f) => ({ label: __(f.label), value: f.erp_field })),
])
function shownColumns(part) {
  const shown = part.options.columns.filter(
    (c) =>
      part.options.fixed[c] ||
      importValue(part.table, c) ||
      showMore.has(part.table + ':' + c),
  )
  // The ones read automatically go last, after what the company chose (as in the Figma)
  return [
    ...shown.filter((c) => !part.options.fixed[c]),
    ...shown.filter((c) => part.options.fixed[c]),
  ]
}
function hiddenColumnOptions(part) {
  const shown = shownColumns(part)
  return [
    { label: __('+ Add an ERP column'), value: '' },
    ...part.options.columns
      .filter((c) => !shown.includes(c))
      .map((c) => ({ label: c, value: c })),
  ]
}

function importValue(table, column) {
  const row = (settings.doc?.[table] || []).find(
    (r) => columnKey(r.erp_column) === columnKey(column),
  )
  return row?.crm_field || ''
}

const newFieldModal = reactive({
  show: false,
  table: '',
  column: '',
  label: '',
  fieldtype: 'Data',
  entity: 'organization',
  loading: false,
})

const fieldTypeOptions = [
  { label: __('Texto curto (Data)'), value: 'Data' },
  { label: __('Texto longo (Text)'), value: 'Small Text' },
  { label: __('Valor monetário (Currency)'), value: 'Currency' },
  { label: __('Número inteiro (Int)'), value: 'Int' },
  { label: __('Número decimal (Float)'), value: 'Float' },
  { label: __('Data (Date)'), value: 'Date' },
  { label: __('Data e hora (Datetime)'), value: 'Datetime' },
  { label: __('Sim / Não (Check)'), value: 'Check' },
]

function importOptions(part) {
  return [
    { label: part.none, value: '' },
    ...part.options.targets,
    { label: __('+ Criar novo campo no CRM…'), value: '__create_new__' },
  ]
}

function openCreateFieldModal(table, column) {
  const cleanName = String(column || '')
    .replace(/[_-]+/g, ' ')
    .toLowerCase()
    .replace(/(^\w|\s\w)/g, (m) => m.toUpperCase())

  newFieldModal.table = table
  newFieldModal.column = column
  newFieldModal.label = cleanName + ' ERP'
  newFieldModal.fieldtype = 'Data'
  newFieldModal.entity = 'organization'
  newFieldModal.loading = false
  newFieldModal.show = true
}

async function submitCreateCustomField() {
  if (!newFieldModal.label?.trim()) return
  newFieldModal.loading = true
  try {
    let targetDoctype = 'CRM Deal Title'
    let prefix = ''
    if (newFieldModal.table !== 'title_field_map') {
      if (newFieldModal.entity === 'contact') {
        targetDoctype = 'Contact'
        prefix = 'contact.'
      } else {
        targetDoctype = 'CRM Organization'
        prefix = 'organization.'
      }
    }
    const res = await call('cred_hub.erp.settings.create_custom_crm_field', {
      target_doctype: targetDoctype,
      label: newFieldModal.label.trim(),
      fieldtype: newFieldModal.fieldtype || 'Data',
    })
    if (res?.ok) {
      toast.success(__('Campo criado com sucesso no CRM!'))
      newFieldModal.show = false
      await loadMapping()
      const targetValue = prefix + res.fieldname
      pickImport(newFieldModal.table, newFieldModal.column, targetValue)
    }
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  } finally {
    newFieldModal.loading = false
  }
}

function pickImport(table, column, value) {
  if (value === '__create_new__') {
    openCreateFieldModal(table, column)
    return
  }
  const rows = (settings.doc[table] || []).filter(
    (r) => columnKey(r.erp_column) !== columnKey(column),
  )
  if (value) rows.push({ erp_column: column, crm_field: value })
  settings.doc[table] = rows
}

// The de-para tables count as changes too (Discard / Not saved)
const mapShape = (doc) =>
  JSON.stringify([
    (doc?.cedente_field_map || []).map((r) => [
      r.erp_field,
      r.source || '',
      r.default_value || '',
    ]),
    (doc?.title_field_map || []).map((r) => [r.erp_column, r.crm_field]),
    (doc?.sacado_field_map || []).map((r) => [r.erp_column, r.crm_field]),
    (doc?.cedente_registry_map || []).map((r) => [r.erp_column, r.crm_field]),
  ])

function isCedenteFieldActive(field) {
  if (field.kind === 'auto') return true
  const row = cedenteRow(field.erp_field)
  if (!row) return false
  if (field.kind === 'list') return Boolean(row.default_value?.trim())
  if (row.source) return true
  return Boolean(row.default_value?.trim())
}

const activeCedenteCount = computed(() =>
  (mapping.value?.cedente.fields || []).filter((f) => isCedenteFieldActive(f))
    .length,
)

const missingRequiredCedente = computed(() => {
  if (!mapping.value?.cedente?.fields) return []
  const mustCheck =
    Boolean(settings.doc?.cedente_send_enabled) ||
    Boolean((settings.doc?.cedente_field_map || []).length)
  if (!mustCheck) return []
  return mapping.value.cedente.fields.filter(
    (f) => f.required === 'yes' && !isCedenteFieldActive(f),
  )
})

function activeImportCount(part) {
  const fixedCount = Object.keys(part.options.fixed || {}).length
  const mappedCount = (settings.doc?.[part.table] || []).filter((r) =>
    Boolean(r.crm_field),
  ).length
  return fixedCount + mappedCount
}

function activeFieldsLabel(count) {
  return count === 1
    ? __('1 active field')
    : __('{0} active fields', [count])
}

function revealAccordionForError(message) {
  const msg = String(message || '')
  if (missingRequiredCedente.value.length > 0) {
    cedenteValidationTriggered.value = true
    openSections.cedente = true
    nextTick(() =>
      cedenteAccordionEl.value?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      }),
    )
    return
  }
  for (const part of importParts.value) {
    const hasColumnInError = (settings.doc?.[part.table] || []).some(
      (r) => r.erp_column && msg.includes(r.erp_column),
    )
    if (hasColumnInError) {
      openSections[part.table] = true
      return
    }
  }
  if (
    (mapping.value?.cedente.fields || []).some(
      (f) => msg.includes(f.erp_field) || msg.includes(__(f.label)),
    )
  ) {
    openSections.cedente = true
  }
}

function save() {
  if (missingRequiredCedente.value.length > 0) {
    cedenteValidationTriggered.value = true
    openSections.cedente = true
    const firstLabel = __(missingRequiredCedente.value[0].label)
    saveError.value = __(
      'The ERP field {0} is required: choose where it comes from.',
      [firstLabel],
    )
    nextTick(() =>
      cedenteAccordionEl.value?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      }),
    )
    return
  }
  const leavingSimulation =
    settings.originalDoc?.sync_dry_run && !settings.doc.sync_dry_run
  if (!leavingSimulation) return submit()
  // Owner decision (credtech#367): read the simulation report before saving for real
  createDialog({
    title: __('Turn off the simulation?'),
    message: __(
      'From the next run the sync saves for real: it creates the cards and títulos and closes the settled ones in the collection funnel. Read the simulation report first.',
    ),
    size: 'md',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Turn off and save'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          submit()
        },
      },
    ],
  })
}

function submit() {
  saveError.value = ''
  settings.save.submit(null, {
    onSuccess: () => {
      cedenteValidationTriggered.value = false
      settings.reload()
      loadMapping()
      connection.value = null
      toast.success(__('ERP settings saved'))
    },
    onError: (err) => {
      const msg = err.messages?.[0] || err.message
      saveError.value = msg
      revealAccordionForError(msg)
    },
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
    if (ok) toast.success(message)
    else toast.error(message)
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  } finally {
    syncing.value = false
  }
}

function resetMapping() {
  createDialog({
    title: __('Restore the default mapping?'),
    message: __(
      'The field mapping goes back to the default of the chosen ERP. Any change your company made to it is lost.',
    ),
    size: 'md',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Restore'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          doResetMapping()
        },
      },
    ],
  })
}

async function doResetMapping() {
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

<style scoped>
/* Figma "Caixa de seleção" (940:108): 20px box, 6px radius, label 14 regular */
.ct-erp-option :deep(input[type='checkbox']) {
  width: 20px;
  height: 20px;
  margin-top: 0;
  border-radius: 6px;
}
.ct-erp-option :deep(label) {
  font-size: 14px;
  line-height: 20px;
  color: var(--ink-gray-9);
}
/* Figma "Botão" with "Ícone à esquerda": 24px icon */
.ct-erp-icon-24 {
  gap: 8px;
}
.ct-erp-icon-24 :deep([class*='lucide-']) {
  width: 24px;
  height: 24px;
}
</style>
