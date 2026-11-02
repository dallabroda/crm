<template>
  <div class="flex flex-col gap-6 p-5 max-w-3xl">
    <!-- Verdict + actions -->
    <div
      class="flex items-center justify-between p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2"
    >
      <div class="flex items-center gap-3">
        <Badge :theme="verdictTheme" variant="solid" size="lg">
          {{ verdictLabel }}
        </Badge>
        <span v-if="org.data?.credit_verdict" class="text-p-sm text-ink-gray-6">
          {{ __('CNPJ') }} {{ org.data?.cnpj || '—' }}
        </span>
      </div>
      <div class="flex gap-2">
        <Button variant="outline" :loading="checking" @click="runCheck(false)">
          {{ __('Check Credit') }}
        </Button>
        <Button
          v-if="org.data?.credit_report"
          variant="outline"
          :loading="checking"
          @click="runCheck(true)"
        >
          {{ __('Force New Check') }}
        </Button>
      </div>
    </div>

    <p v-if="!org.data?.credit_report" class="text-p-sm text-ink-gray-5">
      {{ __('No credit analysis has run for this organization yet.') }}
    </p>

    <template v-if="report.data">
      <!-- Summary -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('CEIS/CNEP Sanctions') }}
          </div>
          <div
            class="text-base-medium"
            :class="
              report.data.ceis_cnep_sanctioned
                ? 'text-ink-red-3'
                : 'text-ink-green-3'
            "
          >
            {{
              report.data.ceis_cnep_verified
                ? report.data.ceis_cnep_sanctioned
                  ? __('Sanctioned')
                  : __('None')
                : __('Not checked')
            }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Lawsuits (as defendant)') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.lawsuits_defendant ?? '—' }} /
            {{ report.data.lawsuits_total ?? '—' }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('PGFN Active Debt') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.pgfn_status || '—' }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Notary Protests (CENPROT)') }}
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
                ? __('{0} found', [report.data.cenprot_protests_count])
                : __('None')
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
            {{ __('Credit Score (DirectD/QUOD)') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.directd_score }} —
            {{ report.data.directd_score_faixa }}
          </div>
        </div>
      </div>
    </template>

    <!-- Credit dossier (credtech#316): the minimum package of queries, then PDF 1 (every return) and PDF 2 (AI opinion) -->
    <div
      v-if="pkg.data"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <div class="flex items-center justify-between">
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Credit dossier')
        }}</span>
        <Badge
          v-if="pkgRunning"
          theme="blue"
          variant="subtle"
          :label="__('Generating…')"
        />
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Generating the dossier makes the queries of the minimum package that are missing, with your own keys, and then creates PDF 1, with every field each provider returned and the original JSON, and PDF 2, the credit opinion written by the AI. Queries made in the last {0} days are reused and not paid again.',
            [pkg.data.reuse_days],
          )
        }}
      </p>
      <div class="space-y-1">
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Minimum package') }}
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
                  : 'text-ink-amber-3'
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
              {{ __('Last attempt failed: {0}', [entry.last_error]) }}
            </div>
          </div>
        </div>
        <div
          v-if="pkg.data.partners_without_cpf.length"
          class="text-p-sm text-ink-gray-5"
        >
          {{
            __('Partners without CPF stay out of the package: {0}.', [
              pkg.data.partners_without_cpf.join(', '),
            ])
          }}
        </div>
      </div>
      <div class="text-p-sm text-ink-gray-7">{{ packageSummary }}</div>
      <div v-if="pkg.data.unavailable.length" class="text-p-sm text-ink-red-3">
        {{
          __(
            'An admin needs to turn these bureaus on or take them out of the package in Settings › Integrations › Credit Bureaus.',
          )
        }}
      </div>
      <div v-if="opinionNote" class="text-p-sm text-ink-amber-3">
        {{ opinionNote }}
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="solid"
          :loading="startingPackage"
          :disabled="!canGeneratePackage"
          @click="askPackage"
        >
          {{ __('Generate dossier (PDF 1 + AI opinion)') }}
        </Button>
      </div>
      <div v-if="dossiers.data && dossiers.data.length" class="space-y-1 pt-2">
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Generated dossiers') }}
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
          __('Credit opinion (AI)')
        }}</span>
        <span v-if="opinionStatus.data" class="text-p-sm text-ink-gray-5">
          {{
            __('{0} of {1} opinions used this month', [
              opinionStatus.data.used,
              opinionStatus.data.included,
            ])
          }}
        </span>
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'The AI reads every query return, the card and the partners, follows the company credit policy and writes a recommendation (approve, approve with reservations or reject) with the risks and strengths, each citing the field and value it came from. It is only a recommendation: the analyst decides.',
          )
        }}
      </p>
      <div
        v-if="opinionStatus.data && !opinionStatus.data.configured"
        class="text-p-sm text-ink-amber-3"
      >
        {{ __('The credit opinion AI is not configured on this site yet.') }}
      </div>
      <div
        v-else-if="
          opinionStatus.data?.next_is_extra &&
          !opinionStatus.data?.extra_allowed
        "
        class="text-p-sm text-ink-amber-3"
      >
        {{
          __(
            'The opinions included this month are used up. An admin can allow paid extra opinions (R$ {0} each) in the Credit settings.',
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
              :label="__('Generating…')"
            />
            <Badge v-else theme="red" variant="subtle" :label="__('Failed')" />
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
              {{ __('Open PDF') }}
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
      <span class="text-lg-semibold text-ink-gray-9">{{ __('Partners') }}</span>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Tick the partners to include in the next query. Every partner query is paid on your provider account. The Receita shows only a masked CPF: use "Find contacts" (Assertiva) or type the CPF.',
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
            :placeholder="__('Full CPF')"
          />
          <Button
            variant="outline"
            size="sm"
            :loading="savingCpf === partner.contact"
            :disabled="!cpfDraft[partner.contact]"
            @click="saveCpf(partner)"
          >
            {{ __('Save CPF') }}
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
          __('Final Bureaus (On-Demand)')
        }}</span>
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Each query is billed by the provider on your own account. CredTech charges nothing.',
          )
        }}
      </p>
      <div
        v-if="options.data.needs_acknowledgement"
        class="p-3 rounded border border-outline-amber-2 bg-surface-amber-1 text-p-sm text-ink-amber-3 space-y-1"
      >
        <div class="font-medium">
          {{ __('Pre-filter: {0}', [verdictText(options.data.verdict)]) }}
        </div>
        <div v-if="options.data.verdict_summary">
          {{ options.data.verdict_summary }}
        </div>
        <div>
          {{
            __('You can still query. You will be asked to confirm the alert.')
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
            <div v-if="!bureau.configured" class="text-p-sm text-ink-amber-3">
              {{ __('Credential missing in the Credit settings.') }}
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
              {{ __('Request for {0} partner(s)', [selectedPartners.length]) }}
            </Button>
            <Button
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key"
              :disabled="!options.data.can_request || !bureau.configured"
              @click="askPremiumBureau(bureau)"
            >
              {{ __('Request') }}
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
        __('Queries made')
      }}</span>
      <div
        v-for="row in results.data"
        :key="row.name"
        class="flex items-center justify-between p-3 border border-outline-gray-2 rounded gap-3"
      >
        <div class="min-w-0">
          <div class="text-base-medium">{{ row.bureau_label }}</div>
          <div class="text-p-sm text-ink-gray-6 truncate">
            {{ row.subject_name || __('Company') }} · {{ row.document }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ row.requested_on }} · {{ row.requested_by }}
          </div>
          <div
            v-if="row.warning_acknowledged"
            class="text-p-sm text-ink-amber-3"
          >
            {{
              __('Queried with the pre-filter alert: {0}', [
                verdictText(row.pre_filter_verdict),
              ])
            }}
          </div>
        </div>
        <Button variant="outline" size="sm" @click="openResult(row)">
          {{ __('View return') }}
        </Button>
      </div>
    </div>

    <Dialog v-model:open="showResult" :title="resultTitle" :size="'4xl'">
      <template #default>
        <p class="text-p-sm text-ink-gray-6 mb-2">
          {{
            __(
              'Complete return, exactly as the provider sent it. Nothing is left out.',
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
    toast.success(__('CPF saved.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not save the CPF.'))
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
    toast.error(err?.messages?.[0] || __('Could not open the return.'))
  }
}

function verdictText(v) {
  if (!v || v === 'Not Checked') return __('Not Checked')
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
    return __('List price {0}, billed by {1} on your account', [
      formatMoney(bureau.price_reference),
      bureau.provider,
    ])
  }
  return __('Billed by {0} on your account, as per your contract', [
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
      __('Credit analysis queued. Refresh in a moment to see the result.'),
    )
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not start the analysis.'))
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
  if (result === 'Approve') return __('Recommendation: approve')
  if (result === 'Reject') return __('Recommendation: reject')
  return __('Recommendation: approve with reservations')
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
    return __('queried on {0}', [formatDate(entry.last_on)])
  if (entry.state === 'unavailable')
    return __('not available: {0}', [entry.reason])
  return entry.price_reference
    ? __('missing · list price {0}, billed by {1} on your account', [
        formatMoney(entry.price_reference),
        entry.provider,
      ])
    : __('missing · billed by {0} on your account, as per your contract', [
        entry.provider,
      ])
}

const packageSummary = computed(() => {
  const data = pkg.data
  if (!data) return ''
  if (!data.missing.length)
    return __(
      'All queries of the minimum package are done. Generating does not cost queries.',
    )
  let text = __(
    'To generate: {0} paid queries, about {1} at list price, billed by the provider on your account. CredTech charges nothing for queries.',
    [data.missing.length, formatMoney(data.missing_cost)],
  )
  if (data.missing_has_contract_price)
    text += ' ' + __('Serasa is billed as per your contract.')
  return text
})

const opinionNote = computed(() => {
  const opinion = pkg.data?.opinion
  if (!opinion) return ''
  if (!opinion.configured)
    return __(
      'The dossier will come without the AI opinion: the credit opinion AI is not configured on this site yet.',
    )
  if (opinion.next_is_extra && !opinion.extra_allowed)
    return __(
      'The dossier will come without the AI opinion: the opinions included this month are used up. An admin can allow paid extra opinions (R$ {0} each) in the Credit settings.',
      [formatPrice(opinion.extra_price)],
    )
  if (opinion.next_is_extra)
    return __(
      'The AI opinion is an extra this month: R$ {0} from the credit wallet.',
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
      __(
        'Paid queries, billed by the provider on your account (CredTech charges nothing): {0}.',
        [
          data.missing
            .map((entry) => `${entry.label} (${entry.subject_name})`)
            .join(', '),
        ],
      ),
    )
    lines.push(__('About {0} at list price.', [formatMoney(data.missing_cost)]))
  }
  if (needsAck) {
    lines.push(
      __('Alert: the pre-filter result for this organization is {0}.', [
        verdictText(data.verdict),
      ]) +
        (data.verdict_summary ? ' ' + data.verdict_summary : '') +
        ' ' +
        __('The query will be recorded as made with the alert.'),
    )
  }
  if (extraOpinion) {
    lines.push(
      __(
        'The opinions included this month are used up. This one costs R$ {0} from the credit wallet (current balance R$ {1}).',
        [formatPrice(opinion.extra_price), formatPrice(opinion.balance)],
      ),
    )
  }
  createDialog({
    title: __('Generate credit dossier'),
    message: lines.join(' '),
    size: 'lg',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: needsAck
          ? __('Query anyway and generate')
          : __('Confirm and generate'),
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
        __('Generating the dossier without the AI opinion: {0}', [
          res.opinion_skipped,
        ]),
      )
    } else {
      toast.success(
        __(
          'Generating the dossier: the queries, PDF 1 and the AI opinion take a few minutes.',
        ),
      )
    }
    opinions.reload()
    startPackagePolling()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not generate the dossier.'))
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
    ? __(
        'This query is paid and billed by {0} on your account (list price {1}). CredTech charges nothing.',
        [bureau.provider, formatMoney(bureau.price_reference)],
      )
    : __(
        'This query is paid and billed by {0} on your account, as per your contract. CredTech charges nothing.',
        [bureau.provider],
      )
  if (partnerList.length) {
    message +=
      ' ' +
      __('Partners: {0}. {1} queries', [
        partnerList.map((partner) => partner.name).join(', '),
        count,
      ]) +
      (bureau.price_reference
        ? ' ' +
          __('(about {0} in total at list price).', [
            formatMoney(bureau.price_reference * count),
          ])
        : '.')
  }
  if (needsAck) {
    message +=
      ' ' +
      __('Alert: the pre-filter result for this organization is {0}.', [
        verdictText(data.verdict),
      ]) +
      (data.verdict_summary ? ' ' + data.verdict_summary : '') +
      ' ' +
      __('The query will be recorded as made with the alert.')
  }
  createDialog({
    title: bureau.label,
    message,
    size: 'lg',
    actions: [
      {
        label: __('Cancel'),
        onClick: ({ close }) => close(),
      },
      {
        label: needsAck ? __('Query anyway (paid)') : __('Confirm paid query'),
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
          __('Could not request the query.'),
      )
    }
  }
  if (done) {
    toast.success(
      targets.length > 1
        ? __('{0} of {1} queries requested.', [done, targets.length])
        : __('Query requested.'),
    )
  }
  failures.forEach((message) => toast.error(message))
  report.reload()
  options.reload()
  results.reload()
  requesting.value = ''
}
</script>
