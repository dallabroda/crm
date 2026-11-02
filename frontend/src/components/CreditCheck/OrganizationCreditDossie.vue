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

      <!-- Dossiê -->
      <div
        class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
      >
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Full Dossier')
        }}</span>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Generates a structured PDF with every section (sanctions, lawsuits, fiscal, protests, score, premium bureaus consulted) and attaches it to this organization.',
            )
          }}
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
    </template>

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
</template>

<script setup>
import { Badge, Button, createResource, call, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const checking = ref(false)
const generatingPdf = ref(false)
const requesting = ref('')

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
  params: { organization_name: props.organizationId },
  auto: true,
})

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

// Transparency (credtech#316): every paid query shows who bills it and the list price; a pre-filter
// other than Pre-Approved does not block, it shows the result and the reason and asks to confirm.
function askPremiumBureau(bureau) {
  const data = options.data
  const needsAck = Boolean(data?.needs_acknowledgement)
  let message = bureau.price_reference
    ? __(
        'This query is paid and billed by {0} on your account (list price {1}). CredTech charges nothing.',
        [bureau.provider, formatMoney(bureau.price_reference)],
      )
    : __(
        'This query is paid and billed by {0} on your account, as per your contract. CredTech charges nothing.',
        [bureau.provider],
      )
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
          requestPremiumBureau(bureau.key, needsAck)
        },
      },
    ],
  })
}

async function requestPremiumBureau(bureau, acknowledged) {
  requesting.value = bureau
  try {
    await call('cred_hub.credit_check.api.request_bureau_final', {
      organization_name: props.organizationId,
      bureau,
      confirm_cost: 1,
      acknowledged_warning: acknowledged ? 1 : 0,
    })
    toast.success(__('Query requested.'))
    report.reload()
    options.reload()
  } catch (err) {
    toast.error(
      err?.messages?.[0] || err?.message || __('Could not request the query.'),
    )
  } finally {
    requesting.value = ''
  }
}
</script>
