<template>
  <SettingsLayoutBase
    :title="__('Credit & Compliance')"
    :description="
      __('Credit analysis rules, fraud prevention and legal queries.')
    "
  >
    <template #header-actions>
      <div v-if="settingsDoc" class="flex items-center gap-2">
        <Button
          variant="solid"
          :loading="saving"
          :disabled="!isDirty"
          @click="saveSettings"
        >
          {{ __('Save') }}
        </Button>
      </div>
    </template>

    <template #content>
      <div v-if="loading" class="flex items-center justify-center mt-[35%]">
        <LoadingIndicator class="size-6" />
      </div>
      <div
        v-else-if="settingsDoc"
        class="ct-credit space-y-6 pb-12 text-ink-gray-8"
      >
        <!-- Who pays (credtech#316): every paid query uses the client's own provider account -->
        <!-- Figma "Configurações · Políticas de Crédito & Compliance"
             (1336:20568): "Aviso de custos" gray box with the info icon -->
        <div
          class="flex gap-2.5 rounded-lg bg-[var(--ct-bg-soft)] px-4 py-3 text-p-base text-ink-gray-6"
        >
          <span class="lucide-info mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            {{
              __(
                "Every paid query uses your own account with each provider: the provider bills you directly and CredTech charges nothing. Prices shown are the providers' list prices, for reference only; your contract may differ.",
              )
            }}
          </span>
        </div>

        <!-- Funnel templates, side by side (credtech#316 + credtech#315): Credit PJ installs here,
             Debt Collection is only read here (the real toggle lives on the Bureaus page) -->
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold leading-6 text-ink-gray-9">
            {{ __('Funnel templates') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Ready funnels to start from: you edit stages, fields and rules afterwards like in any funnel.',
              )
            }}
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">{{
              __('Credit PJ funnel')
            }}</span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'A ready funnel to prospect and analyze credit for companies. Nothing is required by stage and it costs nothing.',
                )
              }}
            </p>
            <p
              v-if="template.data"
              class="text-base font-medium text-ink-gray-9"
            >
              {{ template.data.stages.join(' → ') }}
            </p>
            <div
              v-if="template.data?.installed"
              class="text-base text-[color:var(--ct-success)]"
            >
              {{
                __('Installed: {0}. Edit its stages in the funnel settings.', [
                  template.data.pipeline,
                ])
              }}
            </div>
            <Button
              v-else
              variant="outline"
              :loading="installing"
              @click="installTemplate"
            >
              {{ __('Install the Credit PJ funnel') }}
            </Button>
          </div>

          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">{{
              __('Debt Collection funnel')
            }}</span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Sends overdue titles to protest at the notary (CENPROT) and follows them at the registry every day.',
                )
              }}
            </p>
            <p
              v-if="collectionStatus.data?.stages"
              class="text-base font-medium text-ink-gray-9"
            >
              {{ collectionStatus.data.stages.join(' → ') }}
            </p>
            <div
              v-if="collectionStatus.data?.installed"
              class="text-base text-[color:var(--ct-success)]"
            >
              {{
                __('Installed: {0}. Edit its stages in the funnel settings.', [
                  collectionStatus.data.pipeline,
                ])
              }}
            </div>
            <router-link
              v-else
              :to="{ name: 'Settings', params: { section: 'bureaus' } }"
            >
              <Button variant="outline">
                {{ __('Activate in Notary & Location') }}
              </Button>
            </router-link>
          </div>
        </div>

        <SettingsDivider />
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold leading-6 text-ink-gray-9">
            {{ __('Dossier & AI opinion') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'What the AI follows to write the opinion, and the queries every dossier needs.',
              )
            }}
          </span>
        </div>

        <!-- Credit policy the AI follows (credtech#316): methodology text + parameters, versioned -->
        <div
          class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
        >
          <div class="flex items-center justify-between">
            <span class="text-lg-semibold text-ink-gray-9">{{
              __('Credit policy (AI opinion)')
            }}</span>
            <span v-if="policyDoc" class="text-xs text-ink-gray-6">
              {{
                policyDoc.version
                  ? __('Version {0}', [policyDoc.version])
                  : __('Default policy')
              }}
            </span>
          </div>
          <p class="text-p-xs text-ink-gray-6">
            {{
              __(
                'The AI writes the credit opinion following this methodology. The parameters become automatic alerts in the opinion; they never reject on their own (0 = no limit). Each save creates a new version, and every opinion keeps the version it used.',
              )
            }}
          </p>
          <template v-if="policyDoc">
            <FormControl
              v-model="policyDoc.methodology"
              type="textarea"
              :rows="14"
              :label="__('Methodology')"
            />
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormControl
                v-model.number="policyDoc.parameters.min_company_age_months"
                type="number"
                :label="__('Minimum company age (months, 0 = no limit)')"
              />
              <FormControl
                v-model.number="policyDoc.parameters.max_scr_overdue_percent"
                type="number"
                :label="
                  __('Maximum overdue bank debt in the SCR (%, 0 = no limit)')
                "
              />
            </div>
            <Checkbox
              v-model="policyDoc.parameters.alert_partner_restrictions"
              :label="__('Alert when a partner has restrictions')"
            />
            <div class="flex items-center gap-2">
              <Button
                variant="solid"
                :loading="savingPolicy"
                @click="savePolicy"
              >
                {{ __('Save policy') }}
              </Button>
              <Button variant="subtle" @click="restoreDefaultPolicy">
                {{ __('Restore the default text') }}
              </Button>
            </div>
          </template>
          <div class="pt-3 mt-3 border-t border-outline-gray-2 space-y-1">
            <Checkbox
              v-model="settingsDoc.allow_paid_extra_opinions"
              :label="__('Allow paid extra opinions')"
            />
            <p class="pl-6 text-p-xs text-ink-gray-6">
              {{
                __(
                  'Each company has 30 AI opinions per month included. With this on, from the 31st on each opinion costs R$ 3,00 from the credit wallet, confirmed before it runs. Off, the opinion stops until the next month. Save the settings to apply.',
                )
              }}
            </p>
          </div>
        </div>

        <!-- Minimum package of the credit dossier (credtech#316): the queries every dossier needs -->
        <div
          class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
        >
          <span class="text-lg-semibold text-ink-gray-9">{{
            __('Minimum package of the dossier')
          }}</span>
          <p class="text-p-xs text-ink-gray-6">
            {{
              __(
                'The queries every credit dossier needs. The "Generate dossier" button shows what is missing and its list price, makes the missing queries with your keys after confirmation and then creates PDF 1 and the AI opinion. Only a query of this package that is missing or failed lowers the AI recommendation.',
              )
            }}
          </p>
          <template v-if="packageDoc">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Company') }}
            </div>
            <div
              v-for="opt in packageOptions('company')"
              :key="opt.item"
              class="flex items-center gap-2"
            >
              <Checkbox
                v-model="packageDoc.selected[opt.item]"
                :label="packageOptionLabel(opt)"
              />
              <span v-if="!opt.configured" class="text-p-sm text-ink-amber-3">
                {{
                  opt.enabled
                    ? __('no API credential yet')
                    : __('turn this bureau on below first')
                }}
              </span>
            </div>
            <div class="pt-2 text-base font-semibold text-ink-gray-9">
              {{ __('Each partner with a full CPF') }}
            </div>
            <div
              v-for="opt in packageOptions('partners')"
              :key="opt.item"
              class="flex items-center gap-2"
            >
              <Checkbox
                v-model="packageDoc.selected[opt.item]"
                :label="packageOptionLabel(opt)"
              />
              <span v-if="!opt.configured" class="text-p-sm text-ink-amber-3">
                {{
                  opt.enabled
                    ? __('no API credential yet')
                    : __('turn this bureau on below first')
                }}
              </span>
            </div>
            <FormControl
              v-model.number="packageDoc.reuse_days"
              type="number"
              class="max-w-md"
              :label="
                __(
                  'Reuse queries made up to how many days ago (0 = always query again)',
                )
              "
            />
            <div class="text-base text-ink-gray-9">{{ packageCostText }}</div>
            <Button
              variant="solid"
              :loading="savingPackage"
              @click="savePackage"
            >
              {{ __('Save package') }}
            </Button>
          </template>
        </div>

        <SettingsDivider />
        <div class="flex flex-col gap-1">
          <span class="text-lg font-semibold leading-6 text-ink-gray-9">
            {{ __('Connections & checks') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __('Bureaus, blocks and the automation that triggers the check.')
            }}
          </span>
        </div>

        <!-- Master Enable Switch -->
        <div
          class="flex items-center justify-between gap-4 rounded-lg bg-[var(--ct-bg-soft)] px-5 py-4"
        >
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('Enable risk & compliance analysis') }}
            </span>
            <span class="text-base text-ink-gray-6">
              {{
                __(
                  'Automatic check of lawsuits, federal tax debt, labor debt and notary protests.',
                )
              }}
            </span>
          </div>
          <Switch v-model="settingsDoc.enabled" />
        </div>

        <div v-if="settingsDoc.enabled" class="space-y-6">
          <!-- 0. CGU CEIS/CNEP (step 0, free) -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Step 0: CEIS/CNEP sanctions (CGU)') }}
                </span>
                <Badge :label="__('Free')" theme="green" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.cgu_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Initial check of public sanctions (Portal da Transparência). If the company is sanctioned and the block is on, the analysis is rejected right away.',
                )
              }}
            </p>
            <div v-if="settingsDoc.cgu_enabled" class="pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_ceis_cnep"
                :label="__('Reject right away if listed in CEIS/CNEP')"
              />
            </div>
          </div>

          <!-- 1. Escavador -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Unified lawsuit search (Escavador)') }}
                </span>
                <Badge :label="__('Lawsuits')" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.escavador_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Searches state, federal, labor and higher courts (STJ/STF) across Brazil by CNPJ.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'List price: about {0} per check, billed by Escavador on your account.',
                  [formatMoney(prices.escavador)],
                )
              }}
            </p>
            <div v-if="settingsDoc.escavador_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.escavador_token"
                type="password"
                :label="__('Escavador API token')"
                :placeholder="__('Token from your Escavador account')"
                autocomplete="off"
              />
              <ProviderTest
                v-model="testCnpj.escavador"
                :loading="testing === 'escavador'"
                :disabled="!settingsDoc.escavador_token"
                @test="
                  testProvider(
                    'escavador',
                    'Escavador',
                    settingsDoc.escavador_token,
                  )
                "
              />
            </div>
          </div>

          <!-- 2. Infosimples -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Tax status and federal certificates (Infosimples)') }}
                </span>
                <Badge :label="__('Tax')" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.infosimples_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Federal tax debt (PGFN), Federal CND, labor CNDT and São Paulo notary protests.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'List price: about {0} per check (4 queries), billed by Infosimples on your account.',
                  [formatMoney(prices.infosimples)],
                )
              }}
            </p>
            <div v-if="settingsDoc.infosimples_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.infosimples_token"
                type="password"
                :label="__('Infosimples API token')"
                :placeholder="__('Token from your Infosimples account')"
                autocomplete="off"
              />
              <ProviderTest
                v-model="testCnpj.infosimples"
                :loading="testing === 'infosimples'"
                :disabled="!settingsDoc.infosimples_token"
                @test="
                  testProvider(
                    'infosimples',
                    'Infosimples',
                    settingsDoc.infosimples_token,
                  )
                "
              />
            </div>
          </div>

          <!-- 3. DirectD (QUOD score, nationwide protests, lawsuits) -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Credit score and nationwide protests (DirectD)') }}
                </span>
                <Badge
                  :label="__('Score & notaries')"
                  theme="blue"
                  variant="subtle"
                />
              </div>
              <Switch v-model="settingsDoc.directd_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'QUOD credit score, nationwide notary protests (IEPTB) and lawsuits.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'List price per check: score {0}, protests {1}, lawsuits {2}; FGTS {3} and Sintegra {4} when turned on. Billed by DirectD on your account.',
                  [
                    formatMoney(prices.directd_score),
                    formatMoney(prices.directd_protestos),
                    formatMoney(prices.directd_processos),
                    formatMoney(prices.directd_fgts),
                    formatMoney(prices.directd_sintegra),
                  ],
                )
              }}
            </p>
            <div v-if="usesDirectd" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.directd_token"
                type="password"
                :label="__('DirectD API token')"
                :placeholder="__('Token from your DirectD account')"
                :description="
                  __(
                    'The same token is used for Boa Vista, Dossiê QUOD and SCR Bacen below.',
                  )
                "
                autocomplete="off"
              />
              <ProviderTest
                v-model="testCnpj.directd"
                :loading="testing === 'directd'"
                :disabled="!settingsDoc.directd_token"
                @test="
                  testProvider('directd', 'DirectD', settingsDoc.directd_token)
                "
              />
            </div>
            <div v-if="settingsDoc.directd_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model.number="settingsDoc.min_directd_score"
                type="number"
                :label="__('Minimum score (0 = never reject by score)')"
              />
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <Checkbox
                  v-model="settingsDoc.directd_fgts_enabled"
                  :label="__('Check FGTS status (CRF)')"
                />
                <Checkbox
                  v-model="settingsDoc.directd_sintegra_enabled"
                  :label="__('Check Sintegra / CCC (state registration)')"
                />
              </div>
            </div>
          </div>

          <!-- 4. Funnel automation trigger -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Funnel automation trigger') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Run the check automatically when a card moves to this stage. Each automatic check runs paid queries on your provider accounts.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormControl
                v-model="settingsDoc.auto_trigger_stage"
                type="text"
                :label="__('Trigger stage name')"
                placeholder="ex: Pre-Analysis"
              />
              <div class="flex items-center gap-2 pt-6">
                <Checkbox
                  v-model="settingsDoc.check_second_organization"
                  :label="
                    __('Also check the second organization (sacado), if any')
                  "
                />
              </div>
            </div>
          </div>

          <!-- 5. Risk tolerance and blocks -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Risk criteria and blocks') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Nothing rejects on its own: the system warns and the operator decides. Turn a block on, or set a limit above 0, only if your policy rejects on it.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model.number="settingsDoc.max_lawsuits_defendant"
                type="number"
                :label="
                  __('Maximum lawsuits as defendant (0 = no limit, only warns)')
                "
              />
              <FormControl
                v-model.number="settingsDoc.max_pgfn_debt"
                type="number"
                :label="
                  __(
                    'Maximum tolerated PGFN debt (R$) (0 = no limit, only warns)',
                  )
                "
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="
                  __('Block right away on judicial recovery or bankruptcy')
                "
              />
              <Checkbox
                v-model="settingsDoc.block_on_protest"
                :label="__('Block right away on a notary protest')"
              />
              <Checkbox
                v-if="settingsDoc.directd_fgts_enabled"
                v-model="settingsDoc.block_on_fgts_irregular"
                :label="__('Block if FGTS is irregular')"
              />
            </div>
          </div>

          <!-- 6. Final bureaus (on demand) -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('Full bureau reports (on demand)') }}
              </span>
              <Badge :label="__('On demand')" theme="amber" variant="subtle" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Requested by the operator on the organization. There is no pre-approval lock: before each query the operator sees the pre-filter result, the reason and the cost, and confirms.',
                )
              }}
            </p>
            <Checkbox
              v-model="settingsDoc.serasa_enabled"
              :label="
                __(
                  'Enable Serasa Experian (Advanced PJ Report, your own contract)',
                )
              "
            />
            <div
              v-if="settingsDoc.serasa_enabled"
              class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2"
            >
              <FormControl
                v-model="settingsDoc.serasa_client_id"
                type="text"
                :label="__('Serasa Client ID')"
                autocomplete="off"
              />
              <FormControl
                v-model="settingsDoc.serasa_client_secret"
                type="password"
                :label="__('Serasa Client Secret')"
                autocomplete="off"
              />
              <FormControl
                v-model="settingsDoc.serasa_environment"
                type="select"
                :label="__('Serasa environment')"
                :options="[
                  { label: __('Production'), value: 'Production' },
                  {
                    label: __('Homologation (tests only)'),
                    value: 'Homologation',
                  },
                ]"
              />
              <FormControl
                v-model="settingsDoc.serasa_report_name"
                type="text"
                :label="__('Serasa report name')"
              />
              <div class="md:col-span-2 flex items-center gap-3">
                <Button
                  variant="subtle"
                  :loading="testing === 'serasa'"
                  :disabled="!settingsDoc.serasa_client_id"
                  @click="testSerasa"
                >
                  {{ __('Test login') }}
                </Button>
                <span class="text-p-sm text-ink-gray-5">
                  {{
                    __(
                      'Only signs in to Serasa. It makes no query and costs nothing.',
                    )
                  }}
                </span>
              </div>
            </div>
            <div class="pt-4 mt-4 border-t border-outline-gray-2 space-y-3">
              <p class="text-p-xs text-ink-gray-6">
                {{ __('Through DirectD, with the DirectD token above:') }}
              </p>
              <div
                v-for="bureau in directdBureaus"
                :key="bureau.field"
                class="flex items-center justify-between"
              >
                <Checkbox
                  v-model="settingsDoc[bureau.field]"
                  :label="bureau.label"
                />
                <span v-if="prices" class="text-p-sm text-ink-gray-5">
                  {{ __('List price {0}', [formatMoney(prices[bureau.key])]) }}
                </span>
              </div>
              <p
                v-if="usesDirectd && !settingsDoc.directd_token"
                class="text-p-sm text-ink-amber-3"
              >
                {{ __('Enter the DirectD token above to use these reports.') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  Button,
  FormControl,
  Checkbox,
  Switch,
  Badge,
  LoadingIndicator,
  toast,
  call,
  createResource,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import { createDialog } from '@/utils/dialogs'

// Small inline control: CNPJ for the test + "Test connection" button.
const ProviderTest = {
  props: { modelValue: String, loading: Boolean, disabled: Boolean },
  emits: ['update:modelValue', 'test'],
  setup(props, { emit }) {
    return () =>
      h('div', { class: 'flex items-center gap-2' }, [
        h(FormControl, {
          type: 'text',
          class: 'w-48',
          placeholder: __('CNPJ for the test'),
          modelValue: props.modelValue,
          'onUpdate:modelValue': (value) => emit('update:modelValue', value),
        }),
        h(
          Button,
          {
            variant: 'subtle',
            loading: props.loading,
            disabled: props.disabled || !props.modelValue,
            onClick: () => emit('test'),
          },
          () => __('Test connection'),
        ),
      ])
  },
}

const loading = ref(true)
const saving = ref(false)
const testing = ref('')
const originalDoc = ref(null)

const settingsDoc = ref({
  enabled: false,
  cgu_enabled: false,
  block_on_ceis_cnep: false,
  escavador_enabled: false,
  escavador_token: '',
  infosimples_enabled: false,
  infosimples_token: '',
  directd_enabled: false,
  directd_token: '',
  min_directd_score: 0,
  directd_fgts_enabled: false,
  directd_sintegra_enabled: false,
  auto_trigger_stage: '',
  check_second_organization: true,
  max_lawsuits_defendant: 0,
  max_lawsuit_value: 0,
  block_on_bankruptcy: false,
  max_pgfn_debt: 0,
  block_on_cndt: false,
  block_on_protest: false,
  block_on_fgts_irregular: false,
  serasa_enabled: false,
  serasa_client_id: '',
  serasa_client_secret: '',
  serasa_environment: 'Production',
  serasa_report_name: 'RELATORIO_AVANCADO_PJ_PME',
  boavista_risco_enabled: false,
  dossie_quod_enabled: false,
  scr_bacen_enabled: false,
  allow_paid_extra_opinions: false,
})

const directdBureaus = [
  {
    key: 'boavista_risco',
    field: 'boavista_risco_enabled',
    label: 'Boa Vista - Risco Positivo PJ',
  },
  {
    key: 'dossie_quod',
    field: 'dossie_quod_enabled',
    label: 'Dossiê QUOD - Completo',
  },
  {
    key: 'scr_bacen',
    field: 'scr_bacen_enabled',
    label: 'SCR Analítico - Resumo BACEN',
  },
]

const policyDoc = ref(null)
const savingPolicy = ref(false)
let defaultMethodology = ''

async function loadPolicy() {
  try {
    const res = await call('cred_hub.credit_check.api.get_credit_policy')
    defaultMethodology = res.default_methodology
    policyDoc.value = {
      version: res.version,
      methodology: res.methodology,
      parameters: {
        ...res.parameters,
        alert_partner_restrictions: Boolean(
          res.parameters.alert_partner_restrictions,
        ),
      },
    }
  } catch {
    policyDoc.value = null
  }
}

async function savePolicy() {
  savingPolicy.value = true
  try {
    const res = await call('cred_hub.credit_check.api.save_credit_policy', {
      methodology: policyDoc.value.methodology,
      parameters: JSON.stringify({
        ...policyDoc.value.parameters,
        alert_partner_restrictions: policyDoc.value.parameters
          .alert_partner_restrictions
          ? 1
          : 0,
      }),
    })
    policyDoc.value.version = res.version
    toast.success(__('Credit policy saved (version {0}).', [res.version]))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not save the credit policy.'))
  } finally {
    savingPolicy.value = false
  }
}

function restoreDefaultPolicy() {
  if (policyDoc.value && defaultMethodology) {
    policyDoc.value.methodology = defaultMethodology
  }
}

// Minimum package of the dossier (credtech#316): default Dossiê QUOD + SCR Bacen of the company, 30 days of reuse
const packageDoc = ref(null)
const savingPackage = ref(false)

async function loadPackage() {
  try {
    const res = await call('cred_hub.credit_check.api.get_dossier_package')
    const selected = {}
    for (const opt of res.options)
      selected[opt.item] = res.items.includes(opt.item)
    packageDoc.value = {
      options: res.options,
      selected,
      reuse_days: res.reuse_days,
    }
  } catch {
    packageDoc.value = null
  }
}

function packageOptions(scope) {
  return (packageDoc.value?.options || []).filter((opt) => opt.scope === scope)
}

function packageOptionLabel(opt) {
  return opt.price_reference
    ? `${opt.label} — ${formatMoney(opt.price_reference)}`
    : `${opt.label} — ${__('as per your contract')}`
}

const packageCostText = computed(() => {
  if (!packageDoc.value) return ''
  const chosen = packageDoc.value.options.filter(
    (opt) => packageDoc.value.selected[opt.item],
  )
  const sum = (scope) =>
    chosen
      .filter((opt) => opt.scope === scope)
      .reduce((total, opt) => total + (opt.price_reference || 0), 0)
  let text = __(
    'About {0} per company at list price, billed by the provider on your account.',
    [formatMoney(sum('company'))],
  )
  if (sum('partners'))
    text +=
      ' ' +
      __('Plus {0} for each partner with a CPF.', [
        formatMoney(sum('partners')),
      ])
  if (chosen.some((opt) => !opt.price_reference))
    text += ' ' + __('Serasa is billed as per your contract.')
  return text
})

async function savePackage() {
  savingPackage.value = true
  try {
    const items = Object.keys(packageDoc.value.selected).filter(
      (item) => packageDoc.value.selected[item],
    )
    const res = await call('cred_hub.credit_check.api.save_dossier_package', {
      items: JSON.stringify(items),
      reuse_days: packageDoc.value.reuse_days,
    })
    packageDoc.value.reuse_days = res.reuse_days
    toast.success(__('Minimum package saved.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not save the minimum package.'))
  } finally {
    savingPackage.value = false
  }
}

const template = createResource({
  url: 'cred_hub.credit_check.api.get_credit_template_status',
  auto: true,
})
const installing = ref(false)

// Debt Collection funnel status (credtech#315): read-only here, the toggle lives on the Bureaus page
const collectionStatus = createResource({
  url: 'cred_hub.integrations.protest.collection_funnel_status',
  auto: true,
})

async function installTemplate() {
  installing.value = true
  try {
    await call('cred_hub.credit_check.api.install_credit_template')
    template.reload()
    toast.success(__('Credit PJ funnel installed.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not install the funnel.'))
  } finally {
    installing.value = false
  }
}

const testCnpj = ref({ escavador: '', infosimples: '', directd: '' })

const usesDirectd = computed(
  () =>
    settingsDoc.value.directd_enabled ||
    directdBureaus.some((bureau) => settingsDoc.value[bureau.field]),
)

const isDirty = computed(() => {
  if (!originalDoc.value) return false
  return JSON.stringify(settingsDoc.value) !== JSON.stringify(originalDoc.value)
})

const priceResource = createResource({
  url: 'cred_hub.credit_check.api.get_price_references',
  auto: true,
})
const prices = computed(() => priceResource.data || null)

function formatMoney(value) {
  return `R$ ${Number(value || 0)
    .toFixed(2)
    .replace('.', ',')}`
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await createResource({
      url: 'frappe.client.get',
      params: { doctype: 'Cred Hub Credit Settings' },
    }).fetch()
    if (res) {
      settingsDoc.value = { ...settingsDoc.value, ...res }
      originalDoc.value = JSON.parse(JSON.stringify(settingsDoc.value))
    }
  } catch {
    // If not exists, keep defaults
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'Cred Hub Credit Settings',
      name: 'Cred Hub Credit Settings',
      fieldname: settingsDoc.value,
    })
    originalDoc.value = JSON.parse(JSON.stringify(settingsDoc.value))
    toast.success(__('Credit settings saved successfully!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Failed to save credit settings.'))
  } finally {
    saving.value = false
  }
}

function testProvider(provider, label, token) {
  const cnpj = testCnpj.value[provider]
  if (!token || !cnpj) return
  const cost = prices.value?.test_connection?.[provider]
  createDialog({
    title: __('Test connection'),
    message: __(
      'The test runs a real query on CNPJ {0}, billed by {1} on your account (list price about {2}). CredTech charges nothing.',
      [cnpj, label, formatMoney(cost)],
    ),
    size: 'md',
    actions: [
      {
        label: __('Cancel'),
        onClick: ({ close }) => close(),
      },
      {
        label: __('Run paid test'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          runTest(provider, token, cnpj)
        },
      },
    ],
  })
}

async function testSerasa() {
  testing.value = 'serasa'
  try {
    const res = await call('cred_hub.credit_check.api.test_serasa_connection', {
      client_id: settingsDoc.value.serasa_client_id,
      client_secret: settingsDoc.value.serasa_client_secret,
      environment: settingsDoc.value.serasa_environment,
    })
    if (res?.ok) {
      toast.success(res.message || __('Connection successful!'))
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Connection failed.'))
  } finally {
    testing.value = ''
  }
}

async function runTest(provider, token, cnpj) {
  testing.value = provider
  try {
    const res = await call(
      'cred_hub.credit_check.api.test_provider_connection',
      {
        provider,
        token,
        cnpj,
        confirm_cost: 1,
      },
    )
    if (res?.ok) {
      toast.success(res.message || __('Connection successful!'))
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Connection failed.'))
  } finally {
    testing.value = ''
  }
}

onMounted(() => {
  loadSettings()
  loadPolicy()
  loadPackage()
})
</script>

<style scoped>
/* Figma "Campo": 48px fields, labels 14/500 gray */
.ct-credit :deep(input:not([type='checkbox']):not([type='radio'])),
.ct-credit :deep(select) {
  height: 48px;
  background-color: var(--ct-bg-page);
  border-color: var(--ct-border);
  font-size: 16px;
  padding-inline: 14px;
  border-radius: 6px;
}
.ct-credit :deep(textarea) {
  background-color: var(--ct-bg-page);
  border-color: var(--ct-border);
  font-size: 16px;
  padding: 12px 14px;
  border-radius: 6px;
}
.ct-credit :deep(label.block) {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-gray-6);
}
</style>
