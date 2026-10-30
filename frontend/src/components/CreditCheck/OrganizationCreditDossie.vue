<template>
  <div class="flex flex-col gap-6 p-5 max-w-3xl">
    <!-- Verdict + actions -->
    <div class="flex items-center justify-between p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2">
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
          <div class="text-p-sm text-ink-gray-5">{{ __('CEIS/CNEP Sanctions') }}</div>
          <div class="text-base-medium" :class="report.data.ceis_cnep_sanctioned ? 'text-ink-red-3' : 'text-ink-green-3'">
            {{ report.data.ceis_cnep_verified ? (report.data.ceis_cnep_sanctioned ? __('Sanctioned') : __('None')) : __('Not checked') }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('Lawsuits (as defendant)') }}</div>
          <div class="text-base-medium">{{ report.data.lawsuits_defendant ?? '—' }} / {{ report.data.lawsuits_total ?? '—' }}</div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('PGFN Active Debt') }}</div>
          <div class="text-base-medium">{{ report.data.pgfn_status || '—' }}</div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('Notary Protests (CENPROT)') }}</div>
          <div class="text-base-medium" :class="report.data.cenprot_has_protests ? 'text-ink-red-3' : 'text-ink-green-3'">
            {{ report.data.cenprot_has_protests ? __('{0} found', [report.data.cenprot_protests_count]) : __('None') }}
          </div>
        </div>
        <div class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('FGTS') }}</div>
          <div class="text-base-medium">{{ report.data.fgts_status || '—' }}</div>
        </div>
        <div v-if="report.data.directd_score !== null" class="p-4 border border-outline-gray-2 rounded-lg space-y-1">
          <div class="text-p-sm text-ink-gray-5">{{ __('Credit Score (DirectD/QUOD)') }}</div>
          <div class="text-base-medium">{{ report.data.directd_score }} — {{ report.data.directd_score_faixa }}</div>
        </div>
      </div>

      <!-- Dossiê -->
      <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3">
        <span class="text-lg-semibold text-ink-gray-9">{{ __('Full Dossier') }}</span>
        <p class="text-p-sm text-ink-gray-6">
          {{ __('Generates a structured PDF with every section (sanctions, lawsuits, fiscal, protests, score, premium bureaus consulted) and attaches it to this organization.') }}
        </p>
        <div class="flex items-center gap-2">
          <Button variant="solid" :loading="generatingPdf" @click="generatePdf">
            {{ __('Generate Dossier (PDF)') }}
          </Button>
          <a
            v-if="report.data.dossie_pdf_url"
            :href="report.data.dossie_pdf_url"
            target="_blank"
            class="text-p-sm text-ink-blue-3 underline"
          >
            {{ __('Open last generated PDF') }}
          </a>
        </div>
      </div>

      <!-- Premium bureaus -->
      <div class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4">
        <div class="flex items-center justify-between">
          <span class="text-lg-semibold text-ink-gray-9">{{ __('Final Bureaus (On-Demand)') }}</span>
          <div class="flex items-center gap-2">
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Credit balance') }}: <b>{{ formatMoney(wallet.data?.balance) }}</b>
            </span>
            <Button variant="outline" size="sm" @click="showAddCredits = true">
              {{ __('Add Credits') }}
            </Button>
          </div>
        </div>
        <p v-if="report.data.verdict !== 'Pre-Approved'" class="text-p-sm text-ink-amber-3">
          {{ __('Only available for organizations Pre-Approved in the pre-filter.') }}
        </p>
        <div class="grid grid-cols-1 gap-2">
          <div
            v-for="bureau in premiumBureaus"
            :key="bureau.key"
            class="flex items-center justify-between p-3 border border-outline-gray-2 rounded"
          >
            <div>
              <div class="text-base-medium">{{ bureau.label }}</div>
              <div class="text-p-sm text-ink-gray-5">{{ formatMoney(bureau.price) }}</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key"
              :disabled="report.data.verdict !== 'Pre-Approved'"
              @click="requestPremiumBureau(bureau.key)"
            >
              {{ __('Request') }}
            </Button>
          </div>
          <div class="flex items-center justify-between p-3 border border-outline-gray-2 rounded">
            <div>
              <div class="text-base-medium">{{ __('Serasa Experian (Relato PJ)') }}</div>
              <div class="text-p-sm text-ink-gray-5">{{ __('Billed on your own Serasa contract') }}</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              :loading="requesting === 'serasa'"
              :disabled="report.data.verdict !== 'Pre-Approved'"
              @click="requestPremiumBureau('serasa')"
            >
              {{ __('Request') }}
            </Button>
          </div>
        </div>
      </div>
    </template>

    <AddCreditsModal
      v-model="showAddCredits"
      :min-topup="wallet.data?.min_topup || 10"
      @topup-requested="wallet.reload"
    />
  </div>
</template>

<script setup>
import { Badge, Button, createResource, call, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import AddCreditsModal from '@/components/Modals/AddCreditsModal.vue'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const checking = ref(false)
const generatingPdf = ref(false)
const requesting = ref('')
const showAddCredits = ref(false)

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

const wallet = createResource({
  url: 'cred_hub.billing.get_credit_wallet',
  auto: true,
})

const premiumBureaus = [
  { key: 'boavista_risco', label: 'Boa Vista - Risco Positivo PJ', price: 18.0 },
  { key: 'dossie_quod', label: 'Dossiê QUOD - Completo', price: 10.0 },
  { key: 'scr_bacen', label: 'SCR Analítico - Resumo BACEN', price: 6.0 },
]

const verdictLabel = computed(() => {
  const v = org.data?.credit_verdict
  if (!v || v === 'Not Checked') return __('Not Checked')
  return __(v)
})

const verdictTheme = computed(() => {
  const v = org.data?.credit_verdict
  if (v === 'Rejected') return 'red'
  if (v === 'Warning') return 'amber'
  if (v === 'Pre-Approved') return 'green'
  if (v === 'Error') return 'gray'
  return 'gray'
})

function formatMoney(value) {
  return `R$ ${Number(value || 0).toFixed(2).replace('.', ',')}`
}

async function runCheck(force) {
  checking.value = true
  try {
    await call('cred_hub.credit_check.api.trigger_check', {
      organization_name: props.organizationId,
      force,
    })
    toast.success(__('Credit analysis queued. Refresh in a moment to see the result.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not start the analysis.'))
  } finally {
    checking.value = false
  }
}

async function generatePdf() {
  generatingPdf.value = true
  try {
    const res = await call('cred_hub.credit_check.api.generate_dossie_pdf', {
      organization_name: props.organizationId,
    })
    if (res?.file_url) {
      report.reload()
      window.open(res.file_url, '_blank')
      toast.success(__('Dossier generated and attached to the organization.'))
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Could not generate the dossier.'))
  } finally {
    generatingPdf.value = false
  }
}

async function requestPremiumBureau(bureau) {
  requesting.value = bureau
  try {
    await call('cred_hub.credit_check.api.request_bureau_final', {
      organization_name: props.organizationId,
      bureau,
    })
    toast.success(__('Query requested.'))
    wallet.reload()
    report.reload()
  } catch (err) {
    const message = err?.messages?.[0] || err?.message || ''
    if (message.toLowerCase().includes('insufficient credits')) {
      toast.error(message)
      showAddCredits.value = true
    } else {
      toast.error(message || __('Could not request the query.'))
    }
  } finally {
    requesting.value = ''
  }
}
</script>
