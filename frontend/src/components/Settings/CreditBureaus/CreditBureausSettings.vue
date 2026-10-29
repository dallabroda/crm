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
                placeholder="Insira o token de API do Escavador"
                autocomplete="off"
              />
              <div class="flex items-center gap-2">
                <Button
                  variant="subtle"
                  :loading="testingEscavador"
                  @click="testProvider('escavador', settingsDoc.escavador_token)"
                >
                  {{ __('Test Connection') }}
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
                placeholder="Insira o token de API da Infosimples"
                autocomplete="off"
              />
              <div class="flex items-center gap-2">
                <Button
                  variant="subtle"
                  :loading="testingInfosimples"
                  @click="testProvider('infosimples', settingsDoc.infosimples_token)"
                >
                  {{ __('Test Connection') }}
                </Button>
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
            </div>
          </div>

          <!-- 5. Bureaus Finais (Sob Demanda) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('High-Value Bureaus (On-Demand)') }}
              </span>
              <Badge label="R$ 25 a R$ 40 / Consulta" theme="amber" variant="subtle" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Activated strictly on demand for leads approved in the pre-filter.') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <Checkbox
                v-model="settingsDoc.serasa_enabled"
                :label="__('Enable Serasa Experian (Relato PJ)')"
              />
              <Checkbox
                v-model="settingsDoc.assertiva_enabled"
                :label="__('Enable Assertiva Localize')"
              />
            </div>
          </div>
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
  auto_trigger_stage: '',
  check_second_organization: true,
  max_lawsuits_defendant: 0,
  max_lawsuit_value: 0,
  block_on_bankruptcy: true,
  max_pgfn_debt: 0,
  block_on_cndt: true,
  block_on_protest: true,
  serasa_enabled: false,
  assertiva_enabled: false,
})

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
  if (provider === 'escavador') testingEscavador.value = true
  if (provider === 'infosimples') testingInfosimples.value = true

  try {
    const res = await createResource({
      url: 'cred_hub.credit_check.api.test_provider_connection',
      params: { provider, token },
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
