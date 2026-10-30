<template>
  <SettingsLayoutBase
    :title="__('Credit & Legal Bureaus')"
    :description="__('Configure Escavador API, Infosimples and automated credit analysis.')"
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
      <div v-else-if="settingsDoc" class="space-y-6 pb-12 max-w-4xl text-ink-gray-8">
        <!-- Master Enable Switch -->
        <div class="flex items-center justify-between p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2">
          <div class="flex flex-col gap-0.5">
            <span class="text-base-medium font-semibold text-ink-gray-9">
              {{ __('Enable Credit & Compliance Pipeline') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Active background checking for lawsuits, federal debt, labor debt and protests.') }}
            </span>
          </div>
          <Switch v-model="settingsDoc.enabled" />
        </div>

        <div v-if="settingsDoc.enabled" class="space-y-6">
          <!-- 1. Escavador API (v2) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Escavador API (v2) — Unified Lawsuits') }}
                </span>
                <Badge label="~R$ 0,50 / CNPJ" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.escavador_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Searches state, federal, labor courts and STJ across Brazil in 1 unified call using only the CNPJ.') }}
            </p>
            <div v-if="settingsDoc.escavador_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.escavador_token"
                type="password"
                :label="__('Escavador Bearer Token')"
                :placeholder="__('Enter the Escavador API token')"
                autocomplete="off"
              />
              <div class="flex items-center gap-2">
                <FormControl
                  v-model="testCnpj.escavador"
                  type="text"
                  class="w-48"
                  :placeholder="__('CNPJ to test with')"
                />
                <Button
                  variant="subtle"
                  :loading="testingEscavador"
                  :disabled="!testCnpj.escavador"
                  @click="testProvider('escavador', settingsDoc.escavador_token)"
                >
                  {{ __('Test Connection (real paid query)') }}
                </Button>
              </div>
            </div>
          </div>

          <!-- 2. Infosimples API (v2) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Infosimples API (v2) — Fiscal & Protests') }}
                </span>
                <Badge label="~R$ 0,70 / CNPJ" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.infosimples_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Queries PGFN Active Debt of the Union, CND Federal (Receita/PGFN), CNDT (Labor Court TST) and CENPROT.') }}
            </p>
            <div v-if="settingsDoc.infosimples_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.infosimples_token"
                type="password"
                :label="__('Infosimples API Token')"
                :placeholder="__('Enter the Infosimples API token')"
                autocomplete="off"
              />
              <div class="flex items-center gap-2">
                <FormControl
                  v-model="testCnpj.infosimples"
                  type="text"
                  class="w-48"
                  :placeholder="__('CNPJ to test with')"
                />
                <Button
                  variant="subtle"
                  :loading="testingInfosimples"
                  :disabled="!testCnpj.infosimples"
                  @click="testProvider('infosimples', settingsDoc.infosimples_token)"
                >
                  {{ __('Test Connection (real paid query)') }}
                </Button>
              </div>
            </div>
          </div>

          <!-- 2b. DirectD (Score QUOD + Protestos Nacional + Processos Judiciais) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('DirectD — Score, National Protests & Lawsuits') }}
                </span>
                <Badge label="R$ 1,98 a R$ 2,95 / consulta" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.directd_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('One token covers 3 products: QUOD credit Score (PF/PJ), Protestos Nacional - IEPTB (all of Brazil, unlike the SP-only CENPROT above) and Processos Judiciais - Simplificada.') }}
            </p>
            <div v-if="settingsDoc.directd_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.directd_token"
                type="password"
                :label="__('DirectD Token')"
                :placeholder="__('Enter the DirectD API token')"
                autocomplete="off"
              />
              <FormControl
                v-model.number="settingsDoc.min_directd_score"
                type="number"
                :label="__('Minimum DirectD Score Tolerated (0 = do not reject by score)')"
              />
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <Checkbox
                  v-model="settingsDoc.directd_fgts_enabled"
                  :label="__('Check FGTS regularity (R$ 0,36 / CNPJ)')"
                />
                <Checkbox
                  v-model="settingsDoc.directd_sintegra_enabled"
                  :label="__('Check Sintegra/CCC — state registration (R$ 1,80 / CNPJ)')"
                />
              </div>
            </div>
          </div>

          <!-- 3. Funnel Automation Triggers -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Funnel Stage Automation Trigger') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Automatically execute the R$ 1.20 screening when a card moves to this stage in the sales funnel.') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormControl
                v-model="settingsDoc.auto_trigger_stage"
                type="text"
                :label="__('Trigger Stage Name / Key')"
                placeholder="ex: Pre-Analysis or Compliance"
              />
              <div class="flex items-center gap-2 pt-6">
                <Checkbox
                  v-model="settingsDoc.check_second_organization"
                  :label="__('Check Second Organization (Sacado) if present')"
                />
              </div>
            </div>
          </div>

          <!-- 4. Risk Tolerance & Cutoff Rules -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Risk Tolerances & Automatic Disqualification') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Define criteria to automatically flag cards as Pre-Approved or Rejected.') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model.number="settingsDoc.max_lawsuits_defendant"
                type="number"
                :label="__('Max Lawsuits as Defendant Allowed')"
              />
              <FormControl
                v-model.number="settingsDoc.max_pgfn_debt"
                type="number"
                :label="__('Max PGFN Active Debt Tolerated (R$)')"
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="__('Reject immediately on bankruptcy or judicial recovery')"
              />
              <Checkbox
                v-model="settingsDoc.block_on_protest"
                :label="__('Reject immediately if notary protests exist (CENPROT)')"
              />
              <Checkbox
                v-if="settingsDoc.directd_fgts_enabled"
                v-model="settingsDoc.block_on_fgts_irregular"
                :label="__('Reject immediately if FGTS is irregular')"
              />
            </div>
          </div>

          <!-- 5. Bureau Final (Sob Demanda) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('Final Bureau (On-Demand)') }}
              </span>
              <Badge label="R$ 25 a R$ 40 / Consulta" theme="amber" variant="subtle" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Activated strictly on demand for leads approved in the pre-filter. Uses your own Serasa contract — CredTech never pays for this query.') }}
            </p>
            <Checkbox
              v-model="settingsDoc.serasa_enabled"
              :label="__('Enable Serasa Experian (Relato PJ)')"
            />
            <div v-if="settingsDoc.serasa_enabled" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model="settingsDoc.serasa_endpoint_url"
                type="text"
                :label="__('Serasa Relato PJ Endpoint (your contract)')"
                placeholder="https://..."
              />
              <FormControl
                v-model="settingsDoc.serasa_token"
                type="password"
                :label="__('Serasa Access Token (your contract)')"
                autocomplete="off"
              />
            </div>
            <div v-if="settingsDoc.directd_enabled" class="pt-4 mt-4 border-t border-outline-gray-2 space-y-3">
              <p class="text-p-sm text-ink-gray-6">
                {{ __('These 3 run on the CredTech DirectD account (your DirectD token above) and are resold with a fixed margin.') }}
              </p>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.boavista_risco_enabled"
                  :label="__('Boa Vista - Risco Positivo PJ')"
                />
                <Badge label="custo R$14,03 · cliente R$18,00" theme="amber" variant="subtle" />
              </div>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.dossie_quod_enabled"
                  :label="__('Dossiê QUOD - Completo')"
                />
                <Badge label="custo R$6,99 · cliente R$10,00" theme="amber" variant="subtle" />
              </div>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.scr_bacen_enabled"
                  :label="__('SCR Analítico - Resumo BACEN')"
                />
                <Badge label="custo R$3,90 · cliente R$6,00" theme="amber" variant="subtle" />
              </div>
            </div>
          </div>
          <!-- Assertiva Localize (enriquecimento de contatos) e CENPROT (funil de cobrança) são
          features separadas do épico #290 (módulos 1 e 2) — não fazem parte do pré-filtro de
          crédito e ganham tela própria quando forem implementadas. -->
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Button,
  FormControl,
  Checkbox,
  Switch,
  Badge,
  LoadingIndicator,
  toast,
  createResource,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'

const loading = ref(true)
const saving = ref(false)
const testingEscavador = ref(false)
const testingInfosimples = ref(false)
const originalDoc = ref(null)

const settingsDoc = ref({
  enabled: false,
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
  block_on_bankruptcy: true,
  max_pgfn_debt: 0,
  block_on_cndt: true,
  block_on_protest: true,
  block_on_fgts_irregular: true,
  serasa_enabled: false,
  serasa_endpoint_url: '',
  serasa_token: '',
  boavista_risco_enabled: false,
  dossie_quod_enabled: false,
  scr_bacen_enabled: false,
})

const testCnpj = ref({ escavador: '', infosimples: '' })

const TEST_COST = { escavador: '0,50', infosimples: '0,70' }

const isDirty = computed(() => {
  if (!originalDoc.value) return false
  return JSON.stringify(settingsDoc.value) !== JSON.stringify(originalDoc.value)
})

const getResource = createResource({
  url: 'frappe.client.get_single_value',
  onSuccess: () => {},
})

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
  } catch (err) {
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
  } catch (err) {
    toast.error(__('Failed to save credit settings.'))
  } finally {
    saving.value = false
  }
}

async function testProvider(provider, token) {
  if (!token) {
    toast.error(__('Please enter a token first.'))
    return
  }
  const cnpj = testCnpj.value[provider]
  if (!cnpj) {
    toast.error(__('Enter a CNPJ to run the test query against.'))
    return
  }
  const confirmed = window.confirm(
    __('This runs a real query against {0} and costs about R$ {1}. Continue?').replace('{0}', provider).replace('{1}', TEST_COST[provider])
  )
  if (!confirmed) return

  if (provider === 'escavador') testingEscavador.value = true
  if (provider === 'infosimples') testingInfosimples.value = true

  try {
    const res = await createResource({
      url: 'cred_hub.credit_check.api.test_provider_connection',
      params: { provider, token, cnpj, confirm_cost: true },
    }).submit()
    if (res?.ok) {
      toast.success(res.message || __('Connection successful!'))
    }
  } catch (err) {
    toast.error(err.messages?.[0] || __('Connection failed.'))
  } finally {
    testingEscavador.value = false
    testingInfosimples.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
