<template>
  <div class="flex flex-col gap-6 p-5 max-w-3xl">
    <!-- Verdict + actions -->
    <div
      class="flex flex-col gap-3 p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <span class="text-base font-semibold text-ink-gray-9">
              {{ __('Triagem Jurídica & Fiscal (Pré-Filtro)') }}
            </span>
            <Badge :theme="verdictTheme" variant="solid" size="lg">
              {{ verdictLabel }}
            </Badge>
            <span v-if="org.data?.cnpj" class="text-p-sm text-ink-gray-6">
              {{ __('CNPJ') }} {{ org.data?.cnpj }}
            </span>
          </div>
          <p class="text-p-xs text-ink-gray-6">
            {{
              __(
                'Checagem rápida de Sanções Públicas CEIS/CNEP (CGU · Grátis), Processos Judiciais, Dívida Ativa PGFN, Protestos e FGTS antes de gerar o Dossiê Completo.',
              )
            }}
          </p>
        </div>
        <div class="flex gap-2">
          <Button variant="outline" :loading="checking" @click="runCheck(false)">
            {{ __('Executar Triagem Rápida') }}
          </Button>
          <Button
            v-if="org.data?.credit_report"
            variant="outline"
            :loading="checking"
            @click="runCheck(true)"
          >
            {{ __('Refazer Triagem') }}
          </Button>
        </div>
      </div>
      <div
        v-if="report.data?.verdict_summary"
        class="text-p-xs text-ink-gray-7 bg-surface-white px-3 py-2 rounded border border-outline-gray-1"
      >
        {{ report.data.verdict_summary }}
      </div>
    </div>

    <p v-if="!org.data?.credit_report" class="text-p-sm text-ink-gray-5">
      {{ __('Nenhuma triagem jurídica/fiscal foi executada para esta organização ainda.') }}
    </p>

    <template v-if="report.data">
      <!-- Summary -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Sanções CEIS/CNEP (CGU)') }}
          </div>
          <div
            class="text-base-medium"
            :class="
              !report.data.ceis_cnep_verified
                ? 'text-ink-gray-6'
                : report.data.ceis_cnep_sanctioned
                  ? 'text-ink-red-3'
                  : 'text-ink-green-3'
            "
          >
            {{
              report.data.ceis_cnep_verified
                ? report.data.ceis_cnep_sanctioned
                  ? __('Sancionado')
                  : __('Nenhuma')
                : __('Não verificado')
            }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Processos (como réu)') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.lawsuits_defendant ?? '—' }} /
            {{ report.data.lawsuits_total ?? '—' }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Dívida ativa na PGFN') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.pgfn_status || '—' }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Protestos em cartório (CENPROT)') }}
          </div>
          <div
            class="text-base-medium"
            :class="
              report.data.cenprot_has_protests
                ? 'text-ink-red-3'
                : 'text-ink-green-3'
            "
          >
            {{
              report.data.cenprot_has_protests
                ? __('{0} encontrado(s)', [report.data.cenprot_protests_count])
                : __('Nenhuma')
            }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('FGTS') }}</div>
          <div class="text-base-medium">
            {{ report.data.fgts_status || '—' }}
          </div>
        </div>
        <div
          v-if="report.data.directd_score !== null"
          class="p-4 border border-outline-gray-2 rounded-lg space-y-1"
        >
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Score de Crédito (DirectD/QUOD)') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.directd_score }} —
            {{ report.data.directd_score_faixa }}
          </div>
        </div>
      </div>
    </template>

    <!-- Pasta Digital (Checklist de Documentos) e Relatório de Visita Técnica/Comercial -->
    <CreditOnboardingPanel
      :organization-id="props.organizationId"
      :deal-id="props.dealId"
    />

    <!-- Credit dossier (credtech#316): the minimum package of queries, then PDF 1 (every return) and PDF 2 (AI opinion) -->
    <div
      v-if="pkg.data"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Dossiê de Crédito Completo (Bureaus + Parecer IA)')
        }}</span>
        <Badge
          v-if="pkgRunning"
          theme="blue"
          variant="subtle"
          :label="__('Gerando…')"
        />
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __('Gerar o dossiê executa as consultas do pacote mínimo que faltam usando suas credenciais e gera o PDF 1 (com todos os dados retornados por cada bureau) e o PDF 2 (parecer de crédito redigido pela IA). Consultas feitas nos últimos {0} dias são reaproveitadas sem novo custo.',
            [pkg.data.reuse_days],
          )
        }}
      </p>
      <div class="space-y-1">
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Pacote mínimo configurado') }}
        </div>
        <div
          v-for="entry in pkg.data.items"
          :key="entry.item + (entry.contact || '')"
          class="flex items-start gap-2 text-p-sm"
        >
          <span
            :class="
              entry.state === 'reused'
                ? 'text-ink-green-3'
                : entry.state === 'unavailable'
                  ? 'text-ink-red-3'
                  : 'text-[color:var(--ct-warning)] font-medium'
            "
            >{{ entry.state === 'reused' ? '✓' : '•' }}</span
          >
          <div>
            <span class="text-ink-gray-8"
              >{{ entry.label }} · {{ entry.subject_name }}</span
            >
            <span class="text-ink-gray-5">
              — {{ packageEntryText(entry) }}</span
            >
            <div v-if="entry.last_error" class="text-ink-red-3">
              {{ __('Última tentativa falhou: {0}', [entry.last_error]) }}
            </div>
          </div>
        </div>
        <div
          v-if="pkg.data.partners_without_cpf.length"
          class="text-p-sm text-ink-gray-5"
        >
          {{
            __('Sócios sem CPF completo ficam de fora do pacote: {0}.', [
              pkg.data.partners_without_cpf.join(', '),
            ])
          }}
        </div>
      </div>
      <div class="text-p-sm text-ink-gray-7">{{ packageSummary }}</div>
      <div v-if="pkg.data.unavailable.length" class="text-p-sm text-ink-red-3">
        {{
          __('Um administrador precisa habilitar e configurar o token destes bureaus ou retirá-los do pacote mínimo em Políticas de Crédito & Compliance.',
          )
        }}
      </div>
      <div v-if="opinionNote" class="text-p-sm text-[color:var(--ct-warning)] font-medium">
        {{ opinionNote }}
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="solid"
          :loading="startingPackage"
          :disabled="!canGeneratePackage"
          @click="askPackage"
        >
          {{ __('Gerar Dossiê Completo (PDF 1 + Parecer IA)') }}
        </Button>
      </div>
      <div v-if="dossiers.data && dossiers.data.length" class="space-y-1 pt-2">
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Dossiês gerados') }}
        </div>
        <div
          v-for="file in dossiers.data"
          :key="file.name"
          class="flex items-center gap-2 text-p-sm"
        >
          <a
            :href="file.file_url"
            target="_blank"
            class="text-ink-blue-3 underline truncate"
          >
            {{ file.file_name }}
          </a>
          <span class="text-ink-gray-5">{{ formatDate(file.creation) }}</span>
        </div>
      </div>
    </div>

    <!-- Credit opinion by AI, PDF 2 (credtech#316): a recommendation; the analyst decides. Generated with the dossier -->
    <div
      v-if="opinionStatus.data"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Parecer de Crédito (IA)')
        }}</span>
        <span v-if="opinionStatus.data" class="text-p-sm text-ink-gray-5">
          {{
            __('{0} de {1} pareceres usados neste mês', [
              opinionStatus.data.used,
              opinionStatus.data.included,
            ])
          }}
        </span>
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __('A IA lê todos os retornos dos bureaus, os documentos da Pasta Digital, o Relatório de Visita, o card e os sócios, segue a Política de Crédito da empresa e redige a recomendação fundamentada (aprovar, aprovar com ressalvas ou reprovar). É uma recomendação técnica: a decisão final é do analista/comitê.',
          )
        }}
      </p>
      <div
        v-if="opinionStatus.data && !opinionStatus.data.configured"
        class="text-p-sm text-[color:var(--ct-warning)] font-medium"
      >
        {{ __('A IA de parecer de crédito ainda não está configurada neste ambiente.') }}
      </div>
      <div
        v-else-if="
          opinionStatus.data?.next_is_extra &&
          !opinionStatus.data?.extra_allowed
        "
        class="text-p-sm text-[color:var(--ct-warning)] font-medium"
      >
        {{
          __('Os pareceres incluídos neste mês acabaram. Um administrador pode liberar pareceres extras pagos (R$ {0} cada) nas Configurações de Crédito.',
            [formatPrice(opinionStatus.data.extra_price)],
          )
        }}
      </div>
      <div v-if="opinions.data && opinions.data.length" class="space-y-2 pt-2">
        <div
          v-for="item in opinions.data"
          :key="item.name"
          class="p-3 border border-outline-gray-2 rounded space-y-1"
        >
          <div class="flex items-center gap-2 flex-wrap">
            <Badge
              v-if="item.status === 'Done'"
              :theme="resultTheme(item.result)"
              variant="subtle"
              :label="resultLabel(item.result)"
            />
            <Badge
              v-else-if="item.status === 'Queued'"
              theme="blue"
              variant="subtle"
              :label="__('Gerando…')"
            />
            <Badge v-else theme="red" variant="subtle" :label="__('Falhou')" />
            <span class="text-p-sm text-ink-gray-5">
              {{ formatDate(item.requested_on) }} · {{ item.requested_by }}
            </span>
            <span v-if="item.is_extra" class="text-p-sm text-ink-gray-5">
              · {{ __('extra') }}
            </span>
            <a
              v-if="item.pdf_url"
              :href="item.pdf_url"
              target="_blank"
              class="text-p-sm text-ink-blue-3 underline"
            >
              {{ __('Abrir PDF') }}
            </a>
          </div>
          <div v-if="item.status === 'Done'" class="text-p-sm text-ink-gray-7">
            {{ item.summary }}
          </div>
          <div v-if="item.status === 'Failed'" class="text-p-sm text-ink-red-3">
            {{ item.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Partners (credtech#316): full CPF, and the operator picks who to query; nobody comes ticked -->
    <div
      v-if="partners.data && partners.data.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <span class="text-lg-semibold text-ink-gray-9">{{ __('Quadros Societário (Sócios para Consulta)') }}</span>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __('Marque os sócios para incluir na próxima consulta avulsa. A Receita Federal fornece apenas o CPF mascarado: use "Buscar contatos (Localize)" no topo da Organização ou digite o CPF completo.',
          )
        }}
      </p>
      <div
        v-for="partner in partners.data"
        :key="partner.contact"
        class="flex items-center justify-between p-3 border border-outline-gray-2 rounded gap-3"
      >
        <div class="flex items-center gap-3 min-w-0">
          <input
            type="checkbox"
            class="size-4"
            :checked="selected.includes(partner.contact)"
            :disabled="!partner.has_cpf"
            @change="togglePartner(partner.contact)"
          />
          <div class="min-w-0">
            <div class="text-base-medium truncate">{{ partner.name }}</div>
            <div class="text-p-sm text-ink-gray-5">
              {{ partner.designation }}
              <span v-if="partner.share != null"> · {{ partner.share }}%</span>
            </div>
          </div>
        </div>
        <div v-if="partner.has_cpf" class="text-p-sm text-ink-gray-7">
          {{ partner.cpf }}
        </div>
        <div v-else class="flex items-center gap-2">
          <FormControl
            v-model="cpfDraft[partner.contact]"
            type="text"
            class="w-40"
            :placeholder="__('CPF completo')"
          />
          <Button
            variant="outline"
            size="sm"
            :loading="savingCpf === partner.contact"
            :disabled="!cpfDraft[partner.contact]"
            @click="saveCpf(partner)"
          >
            {{ __('Salvar CPF') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Final bureaus (on demand), with the client's own keys (credtech#316) -->
    <div
      v-if="options.data && options.data.bureaus.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex items-center justify-between">
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Consultas Avulsas nos Bureaus (Sob Demanda)')
        }}</span>
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __('Cada consulta avulsa utiliza a conta da sua empresa no provedor. A CredTech não cobra taxa adicional.',
          )
        }}
      </p>
      <div
        v-if="options.data.needs_acknowledgement"
        class="p-3 rounded border border-outline-amber-2 bg-surface-amber-1 text-p-sm text-[color:var(--ct-warning)] font-medium space-y-1"
      >
        <div class="font-medium">
          {{ __('Triagem rápida: {0}', [verdictText(options.data.verdict)]) }}
        </div>
        <div v-if="options.data.verdict_summary">
          {{ options.data.verdict_summary }}
        </div>
        <div>
          {{
            __('Você ainda pode consultar normalmente (será solicitada confirmação do alerta).')
          }}
        </div>
      </div>
      <div class="grid grid-cols-1 gap-2">
        <div
          v-for="bureau in options.data.bureaus"
          :key="bureau.key"
          class="flex items-center justify-between p-3 border border-outline-gray-2 rounded"
        >
          <div>
            <div class="text-base-medium">{{ bureau.label }}</div>
            <div class="text-p-sm text-ink-gray-5">{{ priceText(bureau) }}</div>
            <div v-if="!bureau.configured" class="text-p-sm text-[color:var(--ct-warning)] font-medium">
              {{ __('Credencial/token ausente nas Configurações de Crédito.') }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Button
              v-if="bureau.partner_ok && selectedPartners.length"
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key + ':partners'"
              :disabled="!options.data.can_request || !bureau.configured"
              @click="askPremiumBureau(bureau, selectedPartners)"
            >
              {{ __('Consultar {0} sócio(s)', [selectedPartners.length]) }}
            </Button>
            <Button
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key"
              :disabled="!options.data.can_request || !bureau.configured"
              @click="askPremiumBureau(bureau)"
            >
              {{ __('Consultar empresa') }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Queries already made, for the company and the partners (credtech#316) -->
    <div
      v-if="results.data && results.data.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <span class="text-lg-semibold text-ink-gray-9">{{
        __('Histórico de Consultas Realizadas')
      }}</span>
      <div
        v-for="row in results.data"
        :key="row.name"
        class="flex items-center justify-between p-3 border border-outline-gray-2 rounded gap-3"
      >
        <div class="min-w-0">
          <div class="text-base-medium">{{ row.bureau_label }}</div>
          <div class="text-p-sm text-ink-gray-6 truncate">
            {{ row.subject_name || __('Empresa') }} · {{ row.document }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ row.requested_on }} · {{ row.requested_by }}
          </div>
          <div
            v-if="row.warning_acknowledged"
            class="text-p-sm text-[color:var(--ct-warning)] font-medium"
          >
            {{
              __('Consultado com alerta de triagem: {0}', [
                verdictText(row.pre_filter_verdict),
              ])
            }}
          </div>
        </div>
        <Button variant="outline" size="sm" @click="openResult(row)">
          {{ __('Ver retorno bruto') }}
        </Button>
      </div>
    </div>

    <Dialog v-model:open="showResult" :title="resultTitle" :size="'4xl'">
      <template #default>
        <p class="text-p-sm text-ink-gray-6 mb-2">
          {{
            __('Retorno completo exatamente como enviado pelo provedor.',
            )
          }}
        </p>
        <pre
          class="text-p-xs bg-surface-gray-2 rounded p-3 overflow-auto max-h-[60vh] whitespace-pre-wrap"
          >{{ resultText }}</pre
        >
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  Dialog,
  FormControl,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'
import CreditOnboardingPanel from '@/components/CreditCheck/CreditOnboardingPanel.vue'

const props = defineProps({
  organizationId: { type: String, required: true },
  // when shown on a card, the queries and comments go to the card (credtech#316)
  dealId: { type: String, default: '' },
})

const checking = ref(false)
const requesting = ref('')
const selected = ref([])
const cpfDraft = reactive({})
const savingCpf = ref('')
const showResult = ref(false)
const resultTitle = ref('')
const resultText = ref('')

const org = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: props.organizationId,
    fieldname: ['credit_verdict', 'credit_report', 'cnpj'],
  },
  auto: true,
  transform: (d) => d?.message || d,
})

const report = createResource({
  url: 'cred_hub.credit_check.api.get_report_details',
  params: { report_name: org.data?.credit_report },
  auto: false,
})

watch(
  () => org.data?.credit_report,
  (reportName) => {
    if (reportName) {
      report.update({ params: { report_name: reportName } })
      report.fetch()
    }
  },
  { immediate: true },
)

// Enabled final bureaus, list prices and the current pre-filter alert (credtech#316)
const options = createResource({
  url: 'cred_hub.credit_check.api.get_final_bureau_options',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
})

// Partners of the company (Contacts) and the queries already made (credtech#316)
const partners = createResource({
  url: 'cred_hub.credit_check.api.get_partners',
  params: { organization_name: props.organizationId },
  auto: true,
})

const results = createResource({
  url: 'cred_hub.credit_check.api.get_bureau_results',
  params: { organization_name: props.organizationId },
  auto: true,
})

// Nobody comes ticked: the operator chooses, and only partners with a valid CPF can be chosen
const selectedPartners = computed(() =>
  (partners.data || []).filter(
    (partner) => partner.has_cpf && selected.value.includes(partner.contact),
  ),
)

function togglePartner(contact) {
  selected.value = selected.value.includes(contact)
    ? selected.value.filter((name) => name !== contact)
    : [...selected.value, contact]
}

async function saveCpf(partner) {
  savingCpf.value = partner.contact
  try {
    await call('cred_hub.credit_check.api.save_partner_cpf', {
      organization_name: props.organizationId,
      contact_name: partner.contact,
      cpf: cpfDraft[partner.contact],
    })
    delete cpfDraft[partner.contact]
    partners.reload()
    toast.success(__('CPF salvo com sucesso.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível salvar o CPF.'))
  } finally {
    savingCpf.value = ''
  }
}

async function openResult(row) {
  try {
    const res = await call('cred_hub.credit_check.api.get_bureau_result', {
      query_name: row.name,
    })
    resultTitle.value = `${res.bureau_label} · ${res.document}`
    resultText.value = JSON.stringify(res.raw, null, 2)
    showResult.value = true
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível abrir o retorno.'))
  }
}

function verdictText(v) {
  if (!v || v === 'Not Checked') return __('Não verificado')
  if (v === 'Pre-Approved') return __('Pré-Aprovado')
  if (v === 'Warning') return __('Atenção')
  if (v === 'Rejected') return __('Reprovado')
  if (v === 'Error') return __('Provedores de triagem não configurados')
  return __(v)
}

const verdictLabel = computed(() => verdictText(org.data?.credit_verdict))

const verdictTheme = computed(() => {
  const v = org.data?.credit_verdict
  if (v === 'Rejected') return 'red'
  if (v === 'Warning') return 'amber'
  if (v === 'Pre-Approved') return 'green'
  return 'gray'
})

function formatMoney(value) {
  return `R$ ${Number(value || 0)
    .toFixed(2)
    .replace('.', ',')}`
}

function priceText(bureau) {
  if (bureau.price_reference) {
    return __('Preço de tabela {0}, cobrado por {1} na sua conta', [
      formatMoney(bureau.price_reference),
      bureau.provider,
    ])
  }
  return __('Cobrado por {0} na sua conta, conforme seu contrato', [
    bureau.provider,
  ])
}

async function runCheck(force) {
  checking.value = true
  try {
    await call('cred_hub.credit_check.api.trigger_check', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      force,
    })
    toast.success(
      __('Triagem enviada para execução. Atualize em instantes para ver o resultado.'),
    )
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível iniciar a triagem.'))
  } finally {
    checking.value = false
  }
}

const dossiers = createResource({
  url: 'cred_hub.credit_check.api.list_credit_dossiers',
  params: { organization_name: props.organizationId },
  auto: true,
})

// AI opinion (PDF 2): counter for the month, list, and polling while one is being generated
const opinionStatus = createResource({
  url: 'cred_hub.credit_check.api.get_credit_opinion_status',
  params: { organization_name: props.organizationId },
  auto: true,
})
const opinions = createResource({
  url: 'cred_hub.credit_check.api.list_credit_opinions',
  params: { organization_name: props.organizationId },
  auto: true,
})
let pollTimer = null
let pollRounds = 0

// Own texts, not bare "Approve"/"Reject": those words already have other global translations
function resultLabel(result) {
  if (result === 'Approve') return __('Recomendação: Aprovar')
  if (result === 'Reject') return __('Recomendação: Reprovar')
  return __('Recomendação: Aprovar com ressalvas')
}

function resultTheme(result) {
  if (result === 'Approve') return 'green'
  if (result === 'Reject') return 'red'
  return 'amber'
}

function formatPrice(value) {
  return Number(value || 0)
    .toFixed(2)
    .replace('.', ',')
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

function startPolling() {
  stopPolling()
  pollRounds = 0
  pollTimer = setInterval(async () => {
    pollRounds += 1
    await opinions.reload()
    const pending = (opinions.data || []).some(
      (item) => item.status === 'Queued',
    )
    if (!pending || pollRounds > 60) {
      stopPolling()
      opinionStatus.reload()
    }
  }, 5000)
}

onBeforeUnmount(stopPolling)

watch(
  () => opinions.data,
  (rows) => {
    if (!pollTimer && (rows || []).some((item) => item.status === 'Queued'))
      startPolling()
  },
)

function formatDate(value) {
  return value ? String(value).slice(0, 16) : ''
}

// Minimum package of the dossier (credtech#316): what is already done in the reuse window, what is missing and its
// list price (billed by the provider on the client's account), then one job runs the queries, PDF 1 and PDF 2
const pkg = createResource({
  url: 'cred_hub.credit_check.api.get_dossier_package_status',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
})
const startingPackage = ref(false)
const packageStarted = ref(false)
let pkgTimer = null
let pkgRounds = 0

const pkgRunning = computed(() =>
  Boolean(pkg.data?.running || packageStarted.value),
)

const canGeneratePackage = computed(() => {
  const data = pkg.data
  return Boolean(data && !pkgRunning.value && !data.unavailable.length)
})

function packageEntryText(entry) {
  if (entry.state === 'reused')
    return __('consultado em {0}', [formatDate(entry.last_on)])
  if (entry.state === 'unavailable')
    return __('indisponível: {0}', [entry.reason])
  return entry.price_reference
    ? __('pendente · preço de tabela {0}, cobrado por {1} na sua conta', [
        formatMoney(entry.price_reference),
        entry.provider,
      ])
    : __('pendente · cobrado por {0} na sua conta, conforme seu contrato', [
        entry.provider,
      ])
}

const packageSummary = computed(() => {
  const data = pkg.data
  if (!data) return ''
  if (!data.missing.length)
    return __('Todas as consultas do pacote mínimo já estão em dia. Gerar o dossiê não consumirá novas consultas.',
    )
  let text = __('Para gerar: {0} consulta(s) paga(s), cerca de {1} pelo preço de tabela, cobrado pelo provedor na sua conta.',
    [data.missing.length, formatMoney(data.missing_cost)],
  )
  if (data.missing_has_contract_price)
    text += ' ' + __('A Serasa é cobrada conforme o seu contrato.')
  return text
})

const opinionNote = computed(() => {
  const opinion = pkg.data?.opinion
  if (!opinion) return ''
  if (!opinion.configured)
    return __('O dossiê será gerado sem o parecer da IA (IA ainda não configurada neste site).',
    )
  if (opinion.next_is_extra && !opinion.extra_allowed)
    return __('O dossiê será gerado sem o parecer da IA: a franquia mensal acabou. Um administrador pode liberar pareceres extras (R$ {0} cada) nas Configurações.',
      [formatPrice(opinion.extra_price)],
    )
  if (opinion.next_is_extra)
    return __('O parecer da IA será avulso neste mês: R$ {0} da carteira de créditos.',
      [formatPrice(opinion.extra_price)],
    )
  return ''
})

function stopPackagePolling() {
  if (pkgTimer) clearInterval(pkgTimer)
  pkgTimer = null
}

// While the job runs: refresh the package, the queries made and the files; the opinion has its own polling
function startPackagePolling() {
  stopPackagePolling()
  pkgRounds = 0
  pkgTimer = setInterval(async () => {
    pkgRounds += 1
    await pkg.reload()
    if (!pkg.data?.running || pkgRounds > 120) {
      packageStarted.value = false
      stopPackagePolling()
      dossiers.reload()
      results.reload()
      opinions.reload()
      opinionStatus.reload()
    }
  }, 5000)
}

onBeforeUnmount(stopPackagePolling)

function askPackage() {
  const data = pkg.data
  if (!data) return
  const opinion = data.opinion || {}
  const extraOpinion =
    opinion.configured && opinion.next_is_extra && opinion.extra_allowed
  const needsAck = Boolean(data.needs_acknowledgement)
  if (!data.missing.length && !extraOpinion) {
    generatePackage(false, false)
    return
  }
  const lines = []
  if (data.missing.length) {
    lines.push(
      __('Consultas pagas, cobradas pelo provedor na sua conta: {0}.',
        [
          data.missing
            .map((entry) => `${entry.label} (${entry.subject_name})`)
            .join(', '),
        ],
      ),
    )
    lines.push(__('Cerca de {0} pelo preço de tabela.', [formatMoney(data.missing_cost)]))
  }
  if (needsAck) {
    lines.push(
      __('Alerta: o resultado da triagem rápida para esta organização é {0}.', [
        verdictText(data.verdict),
      ]) +
        (data.verdict_summary ? ' ' + data.verdict_summary : '') +
        ' ' +
        __('A consulta ficará registrada como realizada sob alerta.'),
    )
  }
  if (extraOpinion) {
    lines.push(
      __('Os pareceres incluídos no mês acabaram. Este parecer custa R$ {0} da carteira de créditos (saldo atual R$ {1}).',
        [formatPrice(opinion.extra_price), formatPrice(opinion.balance)],
      ),
    )
  }
  createDialog({
    title: __('Gerar dossiê de crédito'),
    message: lines.join(' '),
    size: 'lg',
    actions: [
      { label: __('Cancelar'), onClick: ({ close }) => close() },
      {
        label: needsAck
          ? __('Consultar mesmo assim e gerar')
          : __('Confirmar e gerar'),
        variant: 'solid',
        theme: needsAck ? 'red' : 'gray',
        onClick: ({ close }) => {
          close()
          generatePackage(needsAck, extraOpinion)
        },
      },
    ],
  })
}

async function generatePackage(acknowledged, confirmExtra) {
  startingPackage.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.generate_credit_package',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        confirm_cost: 1,
        acknowledged_warning: acknowledged ? 1 : 0,
        confirm_extra_cost: confirmExtra ? 1 : 0,
      },
    )
    packageStarted.value = true
    if (res?.opinion_skipped) {
      toast.warning(
        __('Gerando dossiê sem o parecer da IA: {0}', [
          res.opinion_skipped,
        ]),
      )
    } else {
      toast.success(
        __('Gerando o dossiê: as consultas, o PDF 1 e o parecer da IA levam alguns instantes.',
        ),
      )
    }
    opinions.reload()
    startPackagePolling()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível gerar o dossiê.'))
    pkg.reload()
  } finally {
    startingPackage.value = false
  }
}

// Transparency (credtech#316): every paid query shows who bills it and the list price; a pre-filter
// other than Pre-Approved does not block, it shows the result and the reason and asks to confirm.
function askPremiumBureau(bureau, partnerList = []) {
  const data = options.data
  const needsAck = Boolean(data?.needs_acknowledgement)
  const count = partnerList.length || 1
  let message = bureau.price_reference
    ? __('Esta consulta é paga e cobrada por {0} na sua conta (preço de tabela {1}).',
        [bureau.provider, formatMoney(bureau.price_reference)],
      )
    : __('Esta consulta é paga e cobrada por {0} na sua conta, conforme seu contrato.',
        [bureau.provider],
      )
  if (partnerList.length) {
    message +=
      ' ' +
      __('Sócios: {0}. {1} consulta(s)', [
        partnerList.map((partner) => partner.name).join(', '),
        count,
      ]) +
      (bureau.price_reference
        ? ' ' +
          __('(cerca de {0} no total pelo preço de tabela).', [
            formatMoney(bureau.price_reference * count),
          ])
        : '.')
  }
  if (needsAck) {
    message +=
      ' ' +
      __('Alerta: o resultado da triagem rápida para esta organização é {0}.', [
        verdictText(data.verdict),
      ]) +
      (data.verdict_summary ? ' ' + data.verdict_summary : '') +
      ' ' +
      __('A consulta ficará registrada como realizada sob alerta.')
  }
  createDialog({
    title: bureau.label,
    message,
    size: 'lg',
    actions: [
      {
        label: __('Cancelar'),
        onClick: ({ close }) => close(),
      },
      {
        label: needsAck ? __('Consultar mesmo assim (pago)') : __('Confirmar consulta paga'),
        variant: 'solid',
        theme: needsAck ? 'red' : 'gray',
        onClick: ({ close }) => {
          close()
          requestPremiumBureau(
            bureau.key,
            needsAck,
            partnerList.map((partner) => partner.contact),
          )
        },
      },
    ],
  })
}

// One call per target: the company (no contact) or each ticked partner, one after the other so a
// failure on one never hides the others
async function requestPremiumBureau(bureau, acknowledged, contacts = []) {
  requesting.value = contacts.length ? bureau + ':partners' : bureau
  const targets = contacts.length ? contacts : [null]
  let done = 0
  const failures = []
  for (const contact of targets) {
    try {
      await call('cred_hub.credit_check.api.request_bureau_final', {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        bureau,
        confirm_cost: 1,
        acknowledged_warning: acknowledged ? 1 : 0,
        contact_name: contact,
      })
      done += 1
    } catch (err) {
      failures.push(
        err?.messages?.[0] ||
          err?.message ||
          __('Não foi possível solicitar a consulta.'),
      )
    }
  }
  if (done) {
    toast.success(
      targets.length > 1
        ? __('{0} de {1} consultas solicitadas.', [done, targets.length])
        : __('Consulta realizada com sucesso.'),
    )
  }
  failures.forEach((message) => toast.error(message))
  report.reload()
  options.reload()
  results.reload()
  requesting.value = ''
}
</script>
