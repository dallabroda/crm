<template>
  <div class="flex h-full flex-col gap-6 text-[#1E1F23]">
    <SettingsPageHeader :title="__('Users and Plan')">
      <template #description>
        {{
          __(
            '14 dias de teste grátis com recursos completos e usuários ilimitados. Escolha o plano ideal para sua operação comercial ou de crédito e cobrança.',
          )
        }}
      </template>
    </SettingsPageHeader>

    <div v-if="!data" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="plan.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <div
      v-else-if="data.unlimited"
      class="rounded-[8px] bg-[#E5F1FF] px-3.5 py-2.5 text-base font-medium text-[#0070E0]"
    >
      {{ __('Your company has no user limit.') }}
    </div>

    <div v-else class="flex flex-col gap-6 overflow-y-auto pr-1 pb-6">
      <!-- Resumo de uso e status -->
      <div
        class="flex flex-col gap-3 rounded-[12px] border border-[#E6E7EB] bg-white p-4"
      >
        <div class="flex items-center justify-between gap-4">
          <div class="flex flex-col gap-0.5">
            <div class="flex items-center gap-2">
              <span class="text-lg font-semibold text-[#1E1F23]">
                {{
                  seats.unlimited
                    ? data.in_trial
                      ? __('{0} users, no limit during the trial', [seats.used])
                      : __('{0} active users · Unlimited seats (Enterprise)', [
                          seats.used,
                        ])
                    : __('{0} of {1} users', [seats.used, seats.limit])
                }}
              </span>
              <span
                v-if="currentTierLabel"
                class="rounded-[6px] bg-[#F5F5F7] px-2 py-0.5 text-xs font-medium text-[#5E6068]"
              >
                {{ currentTierLabel }}
              </span>
            </div>
            <span class="text-sm text-[#5E6068]">
              {{
                __('{0} active, {1} invited', [
                  data.used_active,
                  data.used_invited,
                ])
              }}
              <template v-if="data.included_opinions">
                · {{ data.included_opinions }} pareceres IA/mês incluídos
              </template>
            </span>
          </div>
          <Badge
            :label="statusBadge(data.status, data.in_trial).label"
            :theme="statusBadge(data.status, data.in_trial).theme"
            variant="subtle"
            size="lg"
          />
        </div>
        <div
          v-if="!seats.unlimited"
          class="h-1.5 w-full overflow-hidden rounded-full bg-[#EDEDF0]"
        >
          <div
            class="h-full rounded-full"
            :class="seats.full ? 'bg-[#B42318]' : 'bg-[#0088FF]'"
            :style="{ width: barWidth }"
          />
        </div>
        <p
          v-if="seats.full && data.status !== 'Awaiting Payment'"
          class="text-sm text-[#5E6068]"
        >
          {{
            __(
              'All seats are in use. To invite someone else, contract extra users below.',
            )
          }}
        </p>
        <div
          v-if="data.status === 'Active' && data.next_due && data.amount"
          class="text-sm text-[#5E6068]"
        >
          {{
            __('Next charge: {0} on {1}', [
              money(data.amount),
              date(data.next_due),
            ])
          }}
        </div>
      </div>

      <!-- Alertas do plano -->
      <PlanNotice
        v-if="data.in_trial"
        theme="gray"
        :text="
          __(
            'Free trial with unlimited users until {0} ({1}). From {2}, the users above the {3} free one and the extra users you contract are paused, the most recent first, and pending invitations over the limit are no longer valid. To keep them, contract extra users below or choose who stays by deactivating the users you no longer need.',
            [
              date(data.trial_ends_on),
              data.trial_days_left === 1
                ? __('last day')
                : __('{0} days left', [data.trial_days_left]),
              date(dayAfterTrial(data)),
              data.free,
            ],
          )
        "
      />
      <PlanNotice
        v-if="data.status === 'Awaiting Payment'"
        theme="orange"
        :text="
          __(
            'Waiting for the first payment. The plan and extra seats are released as soon as it is confirmed.',
          )
        "
        :invoice-url="data.invoice_url"
      />
      <PlanNotice
        v-if="data.status === 'Past Due'"
        theme="red"
        :text="
          inGrace(data)
            ? __(
                'The monthly payment is overdue. Pay by {0} to keep the extra users.',
                [date(data.grace_until)],
              )
            : __(
                'The monthly payment is overdue. The users above the free ones are paused until it is paid.',
              )
        "
        :invoice-url="data.invoice_url"
      />
      <PlanNotice
        v-if="data.upgrade && !data.upgrade.overdue"
        theme="orange"
        :text="
          __(
            'The new users are already released. Pay the difference by {0}; otherwise only the new users are paused until it is paid.',
            [date(data.upgrade.due_date)],
          )
        "
        :invoice-url="data.upgrade.invoice_url"
      />
      <PlanNotice
        v-if="data.upgrade?.overdue"
        theme="red"
        :text="
          __(
            'The difference was not paid by the due date: the new users are paused until it is paid.',
          )
        "
        :invoice-url="data.upgrade.invoice_url"
      />
      <PlanNotice
        v-if="data.scheduled_from"
        theme="gray"
        :text="
          data.scheduled_extras
            ? __(
                'From {0}, the plan changes to {1} extra users ({2} per month).',
                [
                  date(data.scheduled_from),
                  data.scheduled_extras,
                  money(data.amount),
                ],
              )
            : __(
                'The extra users end on {0}. There are no more charges after that.',
                [date(data.scheduled_from)],
              )
        "
      />

      <div v-if="data.paused_users.length" class="flex flex-col gap-2">
        <div class="text-base font-semibold text-[#1E1F23]">
          {{ __('Paused by the plan') }}
        </div>
        <p class="text-sm text-[#5E6068]">
          {{
            __(
              'Their data is kept. They come back on their own when there is a seat again. You can also choose who stays: deactivate a user and re-enable a paused one.',
            )
          }}
        </p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="user in data.paused_users"
            :key="user.name"
            class="flex items-center gap-2 rounded-[6px] bg-[#F5F5F7] px-2.5 py-1.5 text-sm"
          >
            <span class="font-medium text-[#1E1F23]">{{
              user.full_name || user.name
            }}</span>
            <span class="text-[#8A8C94]">{{ user.name }}</span>
          </li>
        </ul>
      </div>

      <!-- Cards dos 3 Planos -->
      <div class="flex flex-col gap-3 border-t border-[#E6E7EB] pt-5">
        <div class="flex flex-col gap-0.5">
          <div class="text-base font-semibold text-[#1E1F23]">
            Escolha seu plano
          </div>
          <p class="text-sm text-[#5E6068]">
            Selecione o plano ideal para sua equipe. Bureaus pré-pagos continuam
            debitados sob demanda da Carteira de Créditos.
          </p>
        </div>

        <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div
            v-for="tier in PLAN_TIERS"
            :key="tier.id"
            class="relative flex cursor-pointer flex-col justify-between rounded-[12px] border p-4 transition-all"
            :class="
              selectedTier === tier.id
                ? 'border-[#0088FF] bg-[#E5F1FF]/35 ring-1 ring-[#0088FF]'
                : 'border-[#E6E7EB] bg-white hover:border-[#DCDDE2]'
            "
            @click="selectTier(tier.id)"
          >
            <div class="flex flex-col gap-3">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <div class="text-base font-semibold text-[#1E1F23]">
                    {{ tier.name }}
                  </div>
                  <div class="mt-0.5 text-xs text-[#5E6068]">
                    {{ tier.subtitle }}
                  </div>
                </div>
                <span
                  v-if="tier.badge"
                  class="shrink-0 rounded-[6px] bg-[#0088FF] px-2 py-0.5 text-[11px] font-semibold text-white"
                >
                  {{ tier.badge }}
                </span>
              </div>

              <div class="flex items-baseline gap-1 border-b border-[#EDEDF0] pb-3">
                <span class="text-2xl font-bold text-[#1E1F23]">
                  {{ money(tier.basePrice) }}
                </span>
                <span class="text-xs text-[#5E6068]">/mês</span>
              </div>

              <ul class="flex flex-col gap-1.5 text-xs text-[#2A2B30]">
                <li
                  v-for="(feat, idx) in tier.features"
                  :key="idx"
                  class="flex items-start gap-1.5 leading-snug"
                >
                  <span class="mt-0.5 font-bold text-[#0088FF]">✓</span>
                  <span>{{ feat }}</span>
                </li>
              </ul>
            </div>

            <div class="mt-4 pt-2">
              <button
                type="button"
                class="w-full rounded-[8px] px-3 py-2 text-xs font-semibold transition-colors"
                :class="
                  selectedTier === tier.id
                    ? 'bg-[#000000] text-white hover:bg-[#2A2B30]'
                    : 'border border-[#DCDDE2] bg-[#F5F5F7] text-[#1E1F23] hover:bg-[#E6E7EB]'
                "
                @click.stop="selectTier(tier.id)"
              >
                {{
                  selectedTier === tier.id
                    ? 'Plano selecionado'
                    : 'Selecionar ' + tier.name
                }}
              </button>
            </div>
          </div>
        </div>

        <!-- Comparativo completo de funcionalidades -->
        <details
          class="mt-1 rounded-[12px] border border-[#E6E7EB] bg-[#F5F5F7]/60 px-4 py-3"
        >
          <summary
            class="cursor-pointer select-none text-sm font-semibold text-[#1E1F23] hover:text-[#0088FF]"
          >
            Ver tabela comparativa completa de todas as funcionalidades dos 3 planos
          </summary>
          <div class="mt-3 overflow-x-auto">
            <table class="w-full border-collapse text-left text-xs">
              <thead>
                <tr class="border-b border-[#DCDDE2] text-[#5E6068]">
                  <th class="py-2 pr-3 font-semibold">Funcionalidade</th>
                  <th class="px-3 py-2 text-center font-semibold">
                    CRM Vendas (R$ 119)
                  </th>
                  <th
                    class="px-3 py-2 text-center font-semibold text-[#0088FF]"
                  >
                    Crédito & Cobrança (R$ 449)
                  </th>
                  <th class="px-3 py-2 text-center font-semibold">
                    Enterprise (R$ 990)
                  </th>
                </tr>
              </thead>
              <tbody>
                <template
                  v-for="group in PLAN_COMPARISON_GROUPS"
                  :key="group.category"
                >
                  <tr class="bg-[#EDEDF0]/70">
                    <td
                      colspan="4"
                      class="px-2 py-1.5 text-[11px] font-bold uppercase tracking-wide text-[#1E1F23]"
                    >
                      {{ group.category }}
                    </td>
                  </tr>
                  <tr
                    v-for="row in group.rows"
                    :key="row.label"
                    class="border-b border-[#E6E7EB] bg-white"
                  >
                    <td class="py-2 pl-2 pr-3 text-[#2A2B30]">
                      {{ row.label }}
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span
                        v-if="row.vendas === true"
                        class="font-bold text-[#1F7A3D]"
                        >✓</span
                      >
                      <span
                        v-else-if="row.vendas === false"
                        class="text-[#8A8C94]"
                        >—</span
                      >
                      <span v-else class="font-medium text-[#1E1F23]">{{
                        row.vendas
                      }}</span>
                    </td>
                    <td class="bg-[#E5F1FF]/25 px-3 py-2 text-center">
                      <span
                        v-if="row.credito_cobranca === true"
                        class="font-bold text-[#0088FF]"
                        >✓</span
                      >
                      <span
                        v-else-if="row.credito_cobranca === false"
                        class="text-[#8A8C94]"
                        >—</span
                      >
                      <span v-else class="font-semibold text-[#1E1F23]">{{
                        row.credito_cobranca
                      }}</span>
                    </td>
                    <td class="px-3 py-2 text-center">
                      <span
                        v-if="row.enterprise === true"
                        class="font-bold text-[#1F7A3D]"
                        >✓</span
                      >
                      <span
                        v-else-if="row.enterprise === false"
                        class="text-[#8A8C94]"
                        >—</span
                      >
                      <span v-else class="font-medium text-[#1E1F23]">{{
                        row.enterprise
                      }}</span>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </details>
      </div>

      <!-- Configuração de usuários extras e pagamento -->
      <div class="flex flex-col gap-4 border-t border-[#E6E7EB] pt-5">
        <div
          v-if="selectedSpec && !selectedSpec.unlimitedUsers"
          class="flex flex-col gap-2"
        >
          <div class="text-base font-semibold text-[#1E1F23]">
            {{ __('Extra users') }} ({{
              money(selectedSpec.extraUserPrice)
            }}/mês cada)
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <FormControl
              v-model="quantity"
              type="number"
              class="w-40"
              :min="0"
              :max="500"
              :disabled="saving"
            />
            <span class="text-sm font-medium text-[#2A2B30]">
              {{
                __('{0} users in total ({1} included + {2} extra), {3} per month', [
                  selectedSpec.includedUsers + extras,
                  selectedSpec.includedUsers,
                  extras,
                  money(change.monthly),
                ])
              }}
            </span>
          </div>
        </div>
        <div
          v-else-if="selectedSpec?.unlimitedUsers"
          class="rounded-[8px] border border-[#E6E7EB] bg-[#F5F5F7] px-3.5 py-2.5 text-sm text-[#1E1F23]"
        >
          Plano <strong>Enterprise</strong> selecionado:
          <strong>usuários ilimitados</strong> e
          <strong>100 pareceres de IA/mês</strong> por
          <strong>{{ money(change.monthly) }}/mês</strong>.
        </div>

        <ErrorMessage v-if="errors.quantity" :message="errors.quantity" />

        <p v-if="explanation" class="text-sm text-[#5E6068]">
          {{ explanation }}
        </p>
        <p v-if="pausedWarning" class="text-sm text-[#B42318]">
          {{ pausedWarning }}
        </p>

        <template v-if="askPayer">
          <div class="flex flex-col gap-0.5">
            <div class="text-base font-semibold text-[#1E1F23]">
              {{ __('Who pays') }}
            </div>
            <p class="text-sm text-[#5E6068]">
              {{
                __(
                  'Used for the invoice. The card is typed on the payment page, never in Cred Hub.',
                )
              }}
            </p>
          </div>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div v-for="field in payerFields" :key="field.name">
              <FormControl
                v-model="payer[field.name]"
                :type="field.type || 'text'"
                :label="field.label"
                :placeholder="field.placeholder"
                :disabled="saving"
              />
              <ErrorMessage
                v-if="errors[field.name]"
                class="mt-1"
                :message="errors[field.name]"
              />
            </div>
          </div>
        </template>

        <div class="flex justify-end">
          <Button
            variant="solid"
            :label="
              change.kind === 'subscribe' ? __('Save and pay') : __('Save')
            "
            :loading="saving"
            :disabled="change.kind === 'same' || (askPayer && !payerComplete)"
            @click="save"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { formatCurrency } from '@/utils/numberFormat'
import PlanNotice from './PlanNotice.vue'
import {
  PLAN_TIERS,
  PLAN_COMPARISON_GROUPS,
  plan,
  planApi,
  loadPlan,
  usage,
  describeChange,
  chosenExtras,
  chosenTier,
  getTierSpec,
  overLimitAfter,
  statusBadge,
  inGrace,
  openInvoice,
  dayAfterTrial,
} from './planApi'
import { Badge, Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'

const { users } = usersStore()

const data = computed(() => plan.data)
const seats = computed(() => usage(data.value))
const barWidth = computed(() => {
  const { used, limit } = seats.value
  return `${limit ? Math.min(100, (used / limit) * 100) : 0}%`
})

const selectedTier = ref('credito_cobranca')
const selectedSpec = computed(() => getTierSpec(selectedTier.value))

const currentTierLabel = computed(() => {
  if (!data.value) return ''
  if (data.value.in_trial) return 'Teste Grátis (Crédito & Cobrança completo)'
  const t = data.value.plan_tier
  if (!t || t === 'free_legacy') return 'Plano Legado (Grandfathering)'
  return getTierSpec(t)?.name || t
})

const quantity = ref(0)
const extras = computed(() =>
  selectedSpec.value?.unlimitedUsers
    ? 0
    : Math.max(0, parseInt(quantity.value, 10) || 0),
)
const change = computed(() =>
  describeChange(data.value, extras.value, selectedTier.value),
)
const saving = ref(false)
const errors = reactive({})

function selectTier(tierId) {
  selectedTier.value = tierId
  if (tierId === 'enterprise') {
    quantity.value = 0
  }
}

const payer = reactive({
  name: '',
  tax_id: '',
  email: '',
  phone: '',
  postal_code: '',
})
const payerFields = [
  { name: 'name', label: __('Full name or company name') },
  { name: 'tax_id', label: __('CPF or CNPJ') },
  { name: 'email', label: __('E-mail for the invoice'), type: 'email' },
  { name: 'phone', label: __('Phone with area code') },
  { name: 'postal_code', label: __('CEP') },
]
const askPayer = computed(
  () => data.value?.needs_payer && change.value.kind === 'subscribe',
)
const payerComplete = computed(() =>
  payerFields.every((field) => payer[field.name].trim()),
)

const explanation = computed(() => {
  const nextDue = date(data.value?.next_due)
  const monthly = money(change.value.monthly)
  return {
    subscribe: data.value?.in_trial
      ? __(
          'Nothing is charged during the trial: the first invoice is due on {0}, the day after it ends. Unpaid, the extra users are kept until 3 days after that date. Then {1} per month on the same card.',
          [date(dayAfterTrial(data.value)), monthly],
        )
      : __(
          'You pay the first month on the payment page. The plan and seats are released as soon as the payment is confirmed. Then {0} per month on the same card.',
          [monthly],
        ),
    increase: __(
      'The new seats and plan are released now. The prorated difference until {0} goes by payment link, with 3 days to pay (a very small difference goes on the next invoice instead). Then {1} per month.',
      [nextDue, monthly],
    ),
    decrease: __(
      'The seats already paid stay until {0}. From then on, {1} per month.',
      [nextDue, monthly],
    ),
    cancel: __(
      'The seats already paid stay until {0}. There are no more charges after that.',
      [nextDue],
    ),
    keep: __(
      'Keeps the plan and extra users already paid and drops the pending change.',
    ),
    free: __('Back to the {0} free users, with no charges.', [
      data.value?.free,
    ]),
  }[change.value.kind]
})

const pausedWarning = computed(() => {
  const kind = change.value.kind
  if (!['decrease', 'cancel', 'free', 'subscribe'].includes(kind)) return null
  const over = overLimitAfter(data.value, extras.value, selectedTier.value)
  if (!over) return null
  if (data.value.in_trial) {
    return __(
      '{0} users above the new limit are paused on {1}, the most recent first. Nothing is deleted.',
      [over, date(dayAfterTrial(data.value))],
    )
  }
  return kind === 'free'
    ? __(
        '{0} users above the new limit are paused now, the most recent first. Nothing is deleted.',
        [over],
      )
    : __(
        '{0} users above the new limit are paused on {1}, the most recent first. Nothing is deleted.',
        [over, date(data.value.next_due)],
      )
})

watch(
  data,
  (value) => {
    quantity.value = chosenExtras(value)
    selectedTier.value = chosenTier(value)
  },
  { immediate: true },
)

async function save() {
  Object.keys(errors).forEach((key) => delete errors[key])
  saving.value = true
  try {
    const result = await planApi.requestExtraUsers(
      extras.value,
      askPayer.value ? { ...payer } : null,
      selectedTier.value,
    )
    if (!result.ok) {
      errors[result.field] = result.message
      if (!payerFields.some((field) => field.name === result.field)) {
        errors.quantity = result.message
      }
      return
    }
    if (result.invoice_url) {
      openInvoice(result.invoice_url)
      toast.success(
        __('Plan saved. Finish the payment on the page that opened.'),
      )
    } else {
      toast.success(__('Plan saved'))
    }
    await loadPlan()
    users.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Something went wrong'))
  } finally {
    saving.value = false
  }
}

function money(value) {
  return formatCurrency(value || 0, null, data.value?.currency || 'BRL')
}

function date(value) {
  return formatDate(value, 'MMM D, YYYY')
}

onMounted(() => plan.loading || loadPlan())
</script>
