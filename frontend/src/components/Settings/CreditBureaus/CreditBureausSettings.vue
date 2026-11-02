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
        class="space-y-6 pb-12 max-w-4xl text-ink-gray-8"
      >
        <!-- Who pays (credtech#316): every paid query uses the client's own provider account -->
        <div
          class="p-4 rounded-lg border border-outline-gray-2 bg-surface-gray-1 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              "Every paid query uses your own account with each provider: the provider bills you directly and CredTech charges nothing. Prices shown are the providers' list prices, for reference only; your contract may differ.",
            )
          }}
        </div>

        <!-- Credit PJ funnel template (credtech#316) -->
        <div
          class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
        >
          <span class="text-lg-semibold text-ink-gray-9">{{
            __('Credit PJ funnel')
          }}</span>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'A ready funnel to prospect and analyze credit for companies. It is only a starting point: you edit stages, fields and rules like in any funnel. Nothing is required by stage and it costs nothing.',
              )
            }}
          </p>
          <p v-if="template.data" class="text-p-sm text-ink-gray-7">
            {{ template.data.stages.join(' → ') }}
          </p>
          <div
            v-if="template.data?.installed"
            class="text-p-sm text-ink-green-3"
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

        <!-- Master Enable Switch -->
        <div
          class="flex items-center justify-between p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2"
        >
          <div class="flex flex-col gap-0.5">
            <span class="text-base-medium font-semibold text-ink-gray-9">
              {{ __('Enable risk & compliance analysis') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
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
            <p class="text-p-sm text-ink-gray-6">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
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
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Searches state, federal, labor and higher courts (STJ/STF) across Brazil by CNPJ.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-sm text-ink-gray-5">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
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
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Federal tax debt (PGFN), Federal CND, labor CNDT and São Paulo notary protests.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-sm text-ink-gray-5">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
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
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'QUOD credit score, nationwide notary protests (IEPTB) and lawsuits.',
                )
              }}
            </p>
            <p v-if="prices" class="text-p-sm text-ink-gray-5">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Funnel automation trigger') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Risk criteria and blocks') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
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
            class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('Full bureau reports (on demand)') }}
              </span>
              <Badge :label="__('On demand')" theme="amber" variant="subtle" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
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
              <p class="text-p-sm text-ink-gray-6">
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

const template = createResource({
  url: 'cred_hub.credit_check.api.get_credit_template_status',
  auto: true,
})
const installing = ref(false)

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
    await createResource({
      url: 'frappe.client.set_value',
      params: {
        doctype: 'Cred Hub Credit Settings',
        name: 'Cred Hub Credit Settings',
        fieldname: settingsDoc.value,
      },
    }).submit()
    originalDoc.value = JSON.parse(JSON.stringify(settingsDoc.value))
    toast.success(__('Credit settings saved successfully!'))
  } catch {
    toast.error(__('Failed to save credit settings.'))
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
})
</script>
