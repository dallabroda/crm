<template>
  <SettingsLayoutBase
    :title="__('Políticas de Crédito & Compliance')"
    :description="__('Configuração de regras de análise de crédito, prevenção a fraudes e consultas jurídicas.')"
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
              {{ __('Habilitar Análise de Risco & Compliance') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Verificação automatizada de processos, dívida ativa, débitos trabalhistas e protestos.') }}
            </span>
          </div>
          <Switch v-model="settingsDoc.enabled" />
        </div>

        <div v-if="settingsDoc.enabled" class="space-y-6">
          <!-- 0. CGU CEIS/CNEP (Etapa 0, grátis) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Etapa 0 — Sanções CEIS/CNEP (Controladoria-Geral da União)') }}
                </span>
                <Badge label="Incluso" theme="green" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.cgu_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Consulta inicial de sanções públicas (Portal da Transparência). Se a empresa estiver sancionada e o bloqueio estiver ativo, a análise é reprovada imediatamente.') }}
            </p>
            <div v-if="settingsDoc.cgu_enabled" class="pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_ceis_cnep"
                :label="__('Desqualificar imediatamente se constar no CEIS/CNEP')"
              />
            </div>
          </div>

          <!-- 1. Escavador API (v2) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Pesquisa Processual Unificada') }}
                </span>
                <Badge label="Judicial" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.escavador_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Consulta tribunais estaduais, federais, trabalhistas e superiores (STJ/STF) em todo o Brasil usando o CNPJ.') }}
            </p>
            <div v-if="settingsDoc.escavador_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model="settingsDoc.escavador_token"
                type="password"
                :label="__('Token de Acesso da API Judicial')"
                :placeholder="__('Informe o token do provedor judicial')"
                autocomplete="off"
              />
              <div class="flex items-center gap-2">
                <FormControl
                  v-model="testCnpj.escavador"
                  type="text"
                  class="w-48"
                  :placeholder="__('CNPJ para teste')"
                />
                <Button
                  variant="subtle"
                  :loading="testingEscavador"
                  :disabled="!testCnpj.escavador"
                  @click="testProvider('escavador', settingsDoc.escavador_token)"
                >
                  {{ __('Testar Conexão') }}
                </Button>
              </div>
            </div>
          </div>

          <!-- 2. Infosimples API (v2) — conta da CredTech, cobrado via créditos -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Regularidade Fiscal e Certidões Federais') }}
                </span>
                <Badge label="Fiscal" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.infosimples_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Consulta automática de Dívida Ativa da União (PGFN), CND Federal (Receita/PGFN), CNDT (Justiça do Trabalho) e cartórios de protesto.') }}
            </p>
          </div>

          <!-- 2b. DirectD (Score QUOD + Protestos Nacional + Processos Judiciais) — conta da CredTech -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Bureau de Risco e Protestos Nacionais') }}
                </span>
                <Badge label="Score & Cartórios" theme="blue" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.directd_enabled" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Score de Crédito analítico (PJ/PF), abrangência nacional de cartórios (IEPTB Nacional) e apontamentos cadastrais.') }}
            </p>
            <div v-if="settingsDoc.directd_enabled" class="space-y-3 pt-2">
              <FormControl
                v-model.number="settingsDoc.min_directd_score"
                type="number"
                :label="__('Score Mínimo Exigido (0 = não reprovar por score)')"
              />
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <Checkbox
                  v-model="settingsDoc.directd_fgts_enabled"
                  :label="__('Consultar regularidade do FGTS (CRF)')"
                />
                <Checkbox
                  v-model="settingsDoc.directd_sintegra_enabled"
                  :label="__('Consultar Sintegra / CCC (Inscrição Estadual)')"
                />
              </div>
            </div>
          </div>

          <!-- 3. Funnel Automation Triggers -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Gatilho de Automação no Funil') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Executar automaticamente a validação de compliance quando um card for movido para esta etapa.') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormControl
                v-model="settingsDoc.auto_trigger_stage"
                type="text"
                :label="__('Nome da Etapa de Gatilho')"
                placeholder="ex: Pre-Analysis or Compliance"
              />
              <div class="flex items-center gap-2 pt-6">
                <Checkbox
                  v-model="settingsDoc.check_second_organization"
                  :label="__('Verificar Segunda Organização (Sacado), se houver')"
                />
              </div>
            </div>
          </div>

          <!-- 4. Risk Tolerance & Cutoff Rules -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Critérios de Risco e Alçadas de Bloqueio') }}
            </span>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Defina critérios objetivos para pré-aprovação ou recusa automática de operações.') }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model.number="settingsDoc.max_lawsuits_defendant"
                type="number"
                :label="__('Limite de Processos como Réu')"
              />
              <FormControl
                v-model.number="settingsDoc.max_pgfn_debt"
                type="number"
                :label="__('Limite Tolerado de Dívida PGFN (R$)')"
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="__('Bloquear imediatamente se em Recuperação Judicial ou Falência')"
              />
              <Checkbox
                v-model="settingsDoc.block_on_protest"
                :label="__('Bloquear imediatamente se constar Protesto em Cartório')"
              />
              <Checkbox
                v-if="settingsDoc.directd_fgts_enabled"
                v-model="settingsDoc.block_on_fgts_irregular"
                :label="__('Bloquear se FGTS estiver irregular')"
              />
            </div>
          </div>

          <!-- 5. Bureau Final (Sob Demanda) -->
          <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('Relatórios de Bureau Completo (Sob Demanda)') }}
              </span>
              <Badge label="Sob Demanda" theme="amber" variant="subtle" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{ __('Acionamento sob demanda para casos pré-aprovados ou alçadas especiais de análise de crédito.') }}
            </p>
            <Checkbox
              v-model="settingsDoc.serasa_enabled"
              :label="__('Habilitar Serasa Experian (Relato PJ — Contrato Próprio)')"
            />
            <div v-if="settingsDoc.serasa_enabled" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model="settingsDoc.serasa_endpoint_url"
                type="text"
                :label="__('URL de Endpoint do Serasa')"
                placeholder="https://..."
              />
              <FormControl
                v-model="settingsDoc.serasa_token"
                type="password"
                :label="__('Token / Chave de Acesso Serasa')"
                autocomplete="off"
              />
            </div>
            <div class="pt-4 mt-4 border-t border-outline-gray-2 space-y-3">
              <p class="text-p-sm text-ink-gray-6">
                {{ __('Relatórios analíticos especializados acionados sob demanda no cockpit da operação:') }}
              </p>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.boavista_risco_enabled"
                  :label="__('Boa Vista - Risco Positivo PJ')"
                />
                <Badge label="Sob Demanda" theme="amber" variant="subtle" />
              </div>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.dossie_quod_enabled"
                  :label="__('Dossiê QUOD - Completo')"
                />
                <Badge label="Sob Demanda" theme="amber" variant="subtle" />
              </div>
              <div class="flex items-center justify-between">
                <Checkbox
                  v-model="settingsDoc.scr_bacen_enabled"
                  :label="__('SCR Analítico - Resumo BACEN')"
                />
                <Badge label="Sob Demanda" theme="amber" variant="subtle" />
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
const originalDoc = ref(null)

const settingsDoc = ref({
  enabled: false,
  cgu_enabled: false,
  block_on_ceis_cnep: true,
  escavador_enabled: false,
  escavador_token: '',
  infosimples_enabled: false,
  directd_enabled: false,
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

const testCnpj = ref({ escavador: '' })

// test provider

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
    __('Deseja executar uma consulta de teste no provedor para o CNPJ informado?')
  )
  if (!confirmed) return

  testingEscavador.value = true

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
  }
}

onMounted(() => {
  loadSettings()
})
</script>
