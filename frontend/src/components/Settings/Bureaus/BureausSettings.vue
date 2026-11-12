<template>
  <SettingsLayoutBase
    :title="__('Crédito e cobrança')"
    :description="
      __(
        'Contracts of your company with each bureau: every query is paid by your company to the bureau, and every query is kept in the history (LGPD).',
      )
    "
  >
    <!-- the tabs of "Crédito e cobrança" (no sub-items in the menu) -->
    <template #header-top>
      <CreditTabs active="page:bureaus" />
    </template>
    <!-- one Update for the tab: the bureaus and the Régua de cobrança below -->
    <template #header-actions>
      <div v-if="settings.doc && !settings.get.loading" class="flex gap-2">
        <Badge
          v-if="anyDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
        <Button
          v-if="anyDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="discardAll"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="settings.save.loading || reminders?.saving"
          :disabled="!canSave"
          @click="saveAll"
        />
      </div>
    </template>
    <template #content>
      <!-- Figma "Configurações · Cartório & Localização" (1334:19485):
           16/600 section titles, 48px fields, 24px rhythm. Tab "Cartório e
           cobrança": the Régua de cobrança (Figma 2493:4678) comes below. -->
      <div v-if="settings.doc" class="ct-bureaus flex flex-col gap-6">
        <ErrorMessage :message="saveError" />

        <CtAlert type="info">
          {{
            __(
              'Aviso importante: O HubTech CRM fornece exclusivamente a integração técnica com os provedores abaixo. A contratação, o faturamento por consulta e a responsabilidade pelos dados e serviços são diretos entre a sua empresa e cada plataforma (Assertiva ou CENPROT/IEPTB), sem intermediação ou responsabilidade da HubTech.',
            )
          }}
        </CtAlert>

        <!-- Assertiva Localize: partners and their WhatsApp (credtech#290, module 1) -->
        <section class="flex flex-col gap-6">
          <div class="flex items-start justify-between gap-4">
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                Assertiva Localize
              </div>
              <span class="text-base leading-5 text-ink-gray-6">
                {{
                  __(
                    'The Find contacts button of the organization brings each partner as a contact, with CPF, phones (WhatsApp first) and e-mails.',
                  )
                }}
              </span>
              <a
                href="https://assertivasolucoes.com.br"
                target="_blank"
                rel="noopener noreferrer"
                class="text-p-sm text-[color:var(--ct-accent-text)] hover:underline w-fit"
              >
                {{ __('Acessar site oficial da Assertiva Soluções (contratação e suporte) ↗') }}
              </a>
            </div>
            <Switch v-model="assertivaEnabled" size="md" />
          </div>
          <template v-if="settings.doc.assertiva_enabled">
            <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
              <FormControl
                v-model="settings.doc.assertiva_client_id"
                :label="__('Client ID')"
                type="text"
                autocomplete="off"
                required
              />
              <Password
                v-model="settings.doc.assertiva_client_secret"
                :label="__('Client Secret')"
                placeholder="************"
                required
              />
              <FormControl
                v-model="settings.doc.assertiva_purpose"
                type="select"
                :label="__('LGPD purpose of the queries')"
                :options="purposeOptions"
              />
              <FormControl
                v-model="settings.doc.assertiva_cache_days"
                type="number"
                :label="__('Reuse a query for (days)')"
              />
            </div>
            <p class="text-xs text-ink-gray-6">
              {{
                __(
                  'Within this period the saved result is used at no cost, unless someone asks for a new paid query.',
                )
              }}
            </p>
            <FormControl
              v-model="settings.doc.assertiva_partner_lookup"
              type="checkbox"
              :label="
                __(
                  'Also look up the phones and e-mails of each partner (one more paid query per partner)',
                )
              "
              :description="
                __(
                  'Off until you turn it on: each query is paid by your company to Assertiva.',
                )
              "
            />
            <div>
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :label="__('Test connection')"
                icon-left="lucide-plug"
                :loading="testing === 'assertiva'"
                :disabled="isDirty || !settings.originalDoc?.assertiva_enabled"
                @click="test('assertiva')"
              />
            </div>
          </template>
        </section>

        <SettingsDivider />

        <!-- CENPROT: protest at the registry from the collection pipeline (module 2) -->
        <section class="flex flex-col gap-6">
          <div class="flex items-start justify-between gap-4">
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('CENPROT (protest at the registry)') }}
              </div>
              <span class="text-base leading-5 text-ink-gray-6">
                {{
                  __(
                    "Sends overdue titles of the collection pipeline to protest and follows them at the registry every day. Your company's own IEPTB contract; the server IP must be registered at IEPTB.",
                  )
                }}
              </span>
              <div class="flex flex-wrap items-center gap-4 pt-0.5">
                <a
                  href="https://www.pesquisaprotesto.com.br"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-p-sm text-[color:var(--ct-accent-text)] hover:underline"
                >
                  {{ __('Acessar portal oficial CENPROT / IEPTB (contratação e suporte) ↗') }}
                </a>
                <router-link
                  :to="{
                    name: 'Settings',
                    params: { section: 'credit-compliance' },
                  }"
                  class="text-p-sm text-[color:var(--ct-accent-text)] hover:underline"
                >
                  {{ __('Ver o funil Crédito PJ e políticas de compliance →') }}
                </router-link>
              </div>
            </div>
            <Switch v-model="cenprotEnabled" size="md" />
          </div>
          <template v-if="settings.doc.cenprot_enabled">
            <!-- IEPTB only answers registered IPs: the client registers ours in their contract -->
            <!-- Style Guide "Aviso" (960:402), then the IP to copy -->
            <div class="flex flex-col gap-3">
              <CtAlert type="warning">
                {{
                  __(
                    'Before the first title, register this HubTech server IP in your IEPTB contract (CENPROT only answers registered IPs):',
                  )
                }}
              </CtAlert>
              <div class="flex items-center gap-2">
                <TextInput
                  class="ct-field-48 ct-ip w-60"
                  :model-value="serverIp"
                  readonly
                  @focus="$event.target.select()"
                />
                <Button
                  variant="outline"
                  class="ct-btn-accent-text"
                  :label="__('Copy')"
                  icon-left="lucide-copy"
                  :disabled="!serverIp"
                  @click="copyIp"
                />
              </div>
            </div>
            <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
              <FormControl
                v-model="settings.doc.cenprot_environment"
                type="select"
                :label="__('Environment')"
                :options="environmentOptions"
              />
              <FormControl
                v-model="settings.doc.cenprot_username"
                :label="__('CENPROT username')"
                type="text"
                autocomplete="off"
                required
              />
              <Password
                v-model="settings.doc.cenprot_password"
                :label="__('CENPROT password')"
                placeholder="************"
                required
              />
              <FormControl
                v-model="settings.doc.cenprot_presenter_code"
                :label="__('Presenter code (optional)')"
                type="text"
              />
              <FormControl
                v-model="settings.doc.cenprot_bearer_code"
                :label="__('Bearer code (optional)')"
                type="text"
              />
              <FormControl
                v-if="settings.doc.cenprot_bearer_code"
                v-model="settings.doc.cenprot_bearer_name"
                :label="__('Bearer name')"
                type="text"
              />
            </div>

            <div class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('Creditor (who protests)') }}
            </div>
            <div class="ct-field-48 grid grid-cols-3 gap-4 pr-8">
              <FormControl
                v-model="settings.doc.creditor_name"
                class="col-span-2"
                :label="__('Name')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_document"
                :label="__('CPF or CNPJ')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_address"
                class="col-span-2"
                :label="__('Street')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_number"
                :label="__('Number')"
                type="text"
              />
              <FormControl
                v-model="settings.doc.creditor_complement"
                :label="__('Complement')"
                type="text"
              />
              <FormControl
                v-model="settings.doc.creditor_district"
                :label="__('Neighborhood')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_zip"
                :label="__('ZIP code (CEP)')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_city"
                class="col-span-2"
                :label="__('City')"
                type="text"
                required
              />
              <FormControl
                v-model="settings.doc.creditor_state"
                :label="__('State (UF)')"
                type="text"
                maxlength="2"
                required
              />
            </div>

            <div class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('Title defaults') }}
            </div>
            <!-- Sem tipo de título padrão: a espécie é escolhida em cada título (dono, 02/11/2026) -->
            <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
              <FormControl
                v-model="settings.doc.default_endorsement"
                type="select"
                :label="__('Endorsement')"
                :options="endorsementOptions"
              />
            </div>
            <FormControl
              v-model="settings.doc.titles_accepted"
              type="checkbox"
              :label="__('Titles accepted by the debtor')"
            />

            <template v-if="pipeline">
              <div class="flex flex-col gap-1">
                <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                  {{
                    __('Collection pipeline: {0}', [__(pipeline.pipeline_name)])
                  }}
                </div>
                <span class="text-xs text-ink-gray-6">
                  {{
                    __(
                      'When the registry status changes, the card moves to the stage chosen below and the owner gets a notification.',
                    )
                  }}
                </span>
              </div>
              <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
                <FormControl
                  v-model="settings.doc.collection_grouping"
                  type="select"
                  :label="__('Group the cards by')"
                  :options="groupingOptions"
                />
              </div>
              <p class="text-xs text-ink-gray-6">
                {{
                  __(
                    'Used by the spreadsheet import and the ERP synchronization. The cedente is kept on each title either way.',
                  )
                }}
              </p>
              <FormControl
                v-model="settings.doc.auto_send_on_stage"
                type="checkbox"
                :label="
                  __('Send to the registry when a card enters the send stage')
                "
                :description="
                  __(
                    'Off until you turn it on: the registry charges fees for each protest. Without it, titles go only by the Send to protest button of the card.',
                  )
                "
              />
              <FormControl
                v-model="settings.doc.auto_withdraw_on_stage"
                type="checkbox"
                :label="
                  __(
                    'Withdraw or cancel the protest when a card enters the agreement stage',
                  )
                "
                :description="
                  __(
                    'Off until you turn it on: withdrawal and cancellation may have registry fees.',
                  )
                "
              />
              <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
                <FormControl
                  v-for="stage in stageFields"
                  :key="stage.field"
                  v-model="settings.doc[stage.field]"
                  type="select"
                  :label="stage.label"
                  :options="stageOptions"
                />
              </div>
            </template>
            <span v-else class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'The collection pipeline, with its stages, is created when you save.',
                )
              }}
            </span>
            <div>
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :label="__('Test connection')"
                icon-left="lucide-plug"
                :loading="testing === 'cenprot'"
                :disabled="isDirty || !settings.originalDoc?.cenprot_enabled"
                @click="test('cenprot')"
              />
            </div>
          </template>
        </section>
      </div>
      <div
        v-else-if="settings.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
      <section
        v-if="showReminders"
        id="collection-reminders"
        class="mt-6 border-t border-[var(--ct-border)] pt-6"
      >
        <CollectionReminders ref="reminders" embedded />
      </section>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import CreditTabs from '@/components/Settings/CreditBureaus/CreditTabs.vue'
import CollectionReminders from '@/components/Settings/Collection/CollectionReminders.vue'
import '../fieldOutline.css'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import CtAlert from '@/components/CtAlert.vue'
import { useDocument } from '@/data/document'
import { pipelinesStore } from '@/stores/pipelines'
import { FormControl, Switch, TextInput, call, toast } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { scrollToSettingsSection } from '@/composables/settingsNavigation'

// Assertiva Localize and CENPROT (credtech#290), served by the cred_hub app.
// Admins only: the page holds the passwords of the company's contracts.
const DOCTYPE = 'Cred Hub Provider Settings'
const { document: settings } = useDocument(DOCTYPE, DOCTYPE)
const pipelineStore = pipelinesStore()
pipelineStore.ensureLoaded()

const saveError = ref('')
const testing = ref('')
const serverIp = ref('')

watch(
  () => settings.doc?.cenprot_enabled,
  async (enabled) => {
    if (!enabled || serverIp.value) return
    try {
      serverIp.value = (
        await call('cred_hub.integrations.protest.server_ip')
      ).ip
    } catch {
      serverIp.value = ''
    }
  },
  { immediate: true },
)

async function copyIp() {
  await navigator.clipboard.writeText(serverIp.value)
  toast.success(__('Copied'))
}

const FIELDS = [
  'assertiva_enabled',
  'assertiva_client_id',
  'assertiva_client_secret',
  'assertiva_purpose',
  'assertiva_partner_lookup',
  'assertiva_cache_days',
  'cenprot_enabled',
  'cenprot_environment',
  'cenprot_username',
  'cenprot_password',
  'cenprot_presenter_code',
  'cenprot_bearer_code',
  'cenprot_bearer_name',
  'creditor_name',
  'creditor_document',
  'creditor_address',
  'creditor_number',
  'creditor_complement',
  'creditor_district',
  'creditor_city',
  'creditor_state',
  'creditor_zip',
  'collection_grouping',
  'default_endorsement',
  'titles_accepted',
  'auto_send_on_stage',
  'auto_withdraw_on_stage',
  'stage_send',
  'stage_at_registry',
  'stage_notified',
  'stage_protested',
  'stage_paid',
  'stage_agreement',
]

function flag(field) {
  return computed({
    get: () => Boolean(settings.doc?.[field]),
    set: (value) => (settings.doc[field] = value ? 1 : 0),
  })
}
const assertivaEnabled = flag('assertiva_enabled')
const cenprotEnabled = flag('cenprot_enabled')

const normalize = (value) =>
  typeof value === 'boolean' ? String(Number(value)) : String(value ?? '')

const isDirty = computed(() => {
  const doc = settings.doc
  const original = settings.originalDoc
  if (!doc || !original) return false
  return FIELDS.some((f) => normalize(doc[f]) !== normalize(original[f]))
})

const purposeOptions = [
  {
    label: __('Credit protection and collection'),
    value: 'Credit protection and collection',
  },
  {
    label: __('Identity confirmation and fraud prevention'),
    value: 'Identity confirmation and fraud prevention',
  },
]
const environmentOptions = [
  { label: __('Homologation (tests)'), value: 'Homologation' },
  { label: __('Production'), value: 'Production' },
]
const groupingOptions = [
  {
    label: __('Debtor and cedente (one card per pair)'),
    value: 'Debtor and cedente',
  },
  { label: __('Debtor (one card per debtor)'), value: 'Debtor' },
]
const endorsementOptions = [
  { label: __('No endorsement'), value: '' },
  { label: __('Mandate endorsement'), value: 'Mandate endorsement' },
  { label: __('Transfer endorsement'), value: 'Transfer endorsement' },
  { label: __('Blank endorsement'), value: 'Blank endorsement' },
]

const pipeline = computed(() =>
  settings.doc?.collection_pipeline
    ? pipelineStore.getPipeline(settings.doc.collection_pipeline)
    : null,
)
const stageOptions = computed(() => [
  { label: '', value: '' },
  ...(pipeline.value?.stages || []).map((s) => ({
    label: __(s.deal_status),
    value: s.name,
  })),
])
const stageFields = [
  { field: 'stage_send', label: __('Send to the registry stage') },
  { field: 'stage_at_registry', label: __('At the registry stage') },
  { field: 'stage_notified', label: __('Notified by the registry stage') },
  { field: 'stage_protested', label: __('Protested stage') },
  { field: 'stage_paid', label: __('Paid at the registry stage') },
  { field: 'stage_agreement', label: __('Agreement or withdrawn stage') },
]

// the Régua de cobrança section (credtech#367) once the bureaus are loaded;
// /settings/collection-reminders lands here, on #collection-reminders
const route = useRoute()
const reminders = ref(null)
const showReminders = computed(() => Boolean(settings.doc))
// again once the reminders are loaded, as they make the page longer
watch([showReminders, () => reminders.value?.loaded], async ([shown]) => {
  if (!shown || route.hash !== '#collection-reminders') return
  await nextTick()
  scrollToSettingsSection('collection-reminders')
})

const anyDirty = computed(
  () => isDirty.value || Boolean(reminders.value?.changed),
)
const canSave = computed(
  () =>
    anyDirty.value && (!reminders.value?.changed || reminders.value.canSave),
)

function discardAll() {
  if (isDirty.value) settings.reload()
  if (reminders.value?.changed) reminders.value.discard()
}

function saveAll() {
  if (isDirty.value) save()
  if (reminders.value?.changed) reminders.value.save()
}

function save() {
  saveError.value = ''
  const createsPipeline =
    settings.doc.cenprot_enabled && !settings.doc.collection_pipeline
  settings.save.submit(null, {
    onSuccess: () => {
      settings.reload()
      // enabling CENPROT creates the collection pipeline: show it in the menu
      if (createsPipeline) pipelineStore.reload()
      toast.success(__('Bureau settings saved'))
    },
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

async function test(provider) {
  testing.value = provider
  try {
    const module = provider === 'assertiva' ? 'localize' : 'protest'
    const { ok, message } = await call(
      `cred_hub.integrations.${module}.test_connection`,
    )
    ok ? toast.success(message) : toast.error(message)
  } catch (err) {
    toast.error(err.messages?.[0] || err.message)
  } finally {
    testing.value = ''
  }
}
</script>

<style scoped>
/* Figma "Caixa de seleção" (2324:26055): 20px box, 14/20 black label, 12px
   help 26px in */
.ct-bureaus :deep(input[type='checkbox']) {
  width: 20px;
  height: 20px;
  margin-top: 0;
  border-radius: 6px;
}
.ct-bureaus :deep(input[type='checkbox'] + label) {
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  color: var(--ct-text-primary);
}
.ct-bureaus :deep(div:has(> input[type='checkbox']) + div) {
  margin-top: 2px;
  padding-inline-start: 26px;
}
.ct-bureaus :deep(div:has(> input[type='checkbox']) + div p) {
  font-size: 12px;
  line-height: 16px;
}
/* the server IP is read-only: gray box, as in the Figma "IP" (the class
   sits inside TextInput, so it is matched through :deep) */
.ct-bureaus :deep(.ct-ip input) {
  background-color: var(--ct-bg-soft);
  color: var(--ct-text-tertiary);
}
</style>
