<template>
  <!-- Figma "Configurações · Usuários e plano · preenchida" (2201:2060):
       the title lives in the top bar; the page is the plan list and the
       "Adicionais" block, with no intro text, usage card or comparison table. -->
  <div class="flex h-full flex-col gap-6 text-[var(--ct-text-primary)]">
    <SettingsPageHeader :title="__('Users and Plan')" />

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
      class="rounded-[8px] bg-[var(--ct-info-soft)] px-3.5 py-2.5 text-base font-medium text-[var(--ct-info)]"
    >
      {{ __('Your company has no user limit.') }}
    </div>

    <div v-else class="flex flex-col gap-6 overflow-y-auto pb-6">
      <!-- Alertas de pagamento (só aparecem quando há pendência) -->
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

      <!-- Planos · lista -->
      <div
        class="flex flex-col overflow-hidden rounded-[8px] border border-[#EDEDF0] bg-white"
      >
        <div
          v-for="tier in PLAN_TIERS"
          :key="tier.id"
          class="flex items-center gap-4 border-b border-[#EDEDF0] px-6 py-5 last:border-b-0"
        >
          <div
            class="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-[var(--ct-bg-soft)] text-[var(--ct-text-secondary)]"
          >
            <component :is="TIER_ICONS[tier.id]" class="ct-plan-icon size-5" />
          </div>
          <div class="flex min-w-0 flex-1 flex-col gap-1.5">
            <div class="flex items-center gap-2">
              <span class="text-[16px] font-semibold">{{ tier.name }}</span>
              <span
                v-if="tier.id === currentTier"
                class="rounded-full bg-[var(--ct-bg-panel)] px-2.5 py-0.5 text-[12px] font-medium leading-4"
              >
                Plano atual
              </span>
              <span
                v-else-if="tier.badge"
                class="rounded-full bg-[var(--ct-accent-soft)] px-2.5 py-0.5 text-[12px] font-medium leading-4 text-[var(--ct-accent-text)]"
              >
                {{ tier.badge }}
              </span>
            </div>
            <p
              class="text-[14px] leading-[normal] text-[var(--ct-text-secondary)]"
            >
              {{ tierDescription(tier) }}
            </p>
          </div>
          <div class="flex shrink-0 items-baseline gap-1 whitespace-nowrap">
            <span class="text-[16px] font-semibold leading-6">
              {{ price(tier.basePrice) }}
            </span>
            <span class="text-[14px] text-[var(--ct-text-secondary)]"
              >/mês</span
            >
          </div>
          <button
            v-if="tier.id === currentTier"
            type="button"
            disabled
            class="flex h-10 w-[220px] shrink-0 items-center justify-center rounded-[6px] bg-[var(--ct-bg-panel)] px-6 text-[14px] font-semibold opacity-40"
          >
            Plano atual
          </button>
          <button
            v-else-if="tier.id === selectedTier"
            type="button"
            class="flex h-10 w-[220px] shrink-0 items-center justify-center rounded-[6px] border border-[var(--ct-border)] bg-white px-6 text-[14px] font-semibold hover:bg-[var(--ct-bg-soft)]"
            @click="selectTier(currentTier || tier.id)"
          >
            Plano escolhido
          </button>
          <button
            v-else
            type="button"
            class="flex h-10 w-[220px] shrink-0 items-center justify-center rounded-[6px] bg-[var(--ct-accent)] px-6 text-[14px] font-semibold text-white hover:bg-[var(--ct-accent-hover)] disabled:opacity-40"
            :disabled="saving"
            @click="selectTier(tier.id)"
          >
            Mudar para {{ tier.name }}
          </button>
        </div>
      </div>

      <!-- Adicionais -->
      <div
        v-if="selectedSpec"
        class="flex flex-col gap-4 rounded-[8px] border border-[#EDEDF0] bg-white p-6"
      >
        <div class="text-[14px] font-medium">Adicionais</div>
        <div class="flex items-center gap-4">
          <div
            class="flex size-10 shrink-0 items-center justify-center rounded-[8px] bg-[var(--ct-bg-soft)] text-[#2A2B30]"
          >
            <UsersIcon class="ct-plan-icon size-5" />
          </div>
          <div
            class="flex min-w-0 flex-1 flex-col gap-1 text-[14px] leading-[normal]"
          >
            <span class="font-medium">{{ __('Extra users') }}</span>
            <span class="text-[var(--ct-text-secondary)]">
              {{ extrasDescription }}
            </span>
          </div>
          <template v-if="!selectedSpec.unlimitedUsers">
            <div
              class="flex shrink-0 overflow-hidden rounded-[6px] border border-[var(--ct-border)] bg-white text-[14px]"
            >
              <button
                type="button"
                class="flex h-8 w-9 items-center justify-center bg-[var(--ct-bg-soft)] font-semibold hover:bg-[var(--ct-bg-panel)]"
                aria-label="Remover um usuário extra"
                :disabled="saving || extras <= 0"
                @click="quantity = Math.max(0, extras - 1)"
              >
                −
              </button>
              <input
                v-model.number="quantity"
                type="number"
                min="0"
                max="500"
                class="ct-stepper-value h-8 w-9 border-0 p-0 text-center text-[14px] font-medium focus:ring-0"
                :aria-label="__('Extra users')"
                :disabled="saving"
              />
              <button
                type="button"
                class="flex h-8 w-9 items-center justify-center bg-[var(--ct-bg-soft)] font-semibold hover:bg-[var(--ct-bg-panel)] disabled:opacity-40"
                aria-label="Adicionar um usuário extra"
                :disabled="saving || extras >= 500"
                @click="quantity = Math.min(500, extras + 1)"
              >
                +
              </button>
            </div>
            <span
              class="shrink-0 whitespace-nowrap text-[14px] font-medium text-[var(--ct-text-secondary)]"
            >
              + {{ price(selectedSpec.extraUserPrice) }}/mês cada
            </span>
          </template>
        </div>
        <div class="flex items-start justify-between whitespace-nowrap">
          <span class="text-[14px] font-medium">Total estimado</span>
          <span class="text-[16px] font-semibold leading-6">
            {{ money(change.monthly) }}/mês
          </span>
        </div>
      </div>

      <!-- Confirmação da mudança (só quando algo mudou) -->
      <div v-if="change.kind !== 'same'" class="flex flex-col gap-4">
        <ErrorMessage v-if="errors.quantity" :message="errors.quantity" />

        <p v-if="explanation" class="text-sm text-[var(--ct-text-secondary)]">
          {{ explanation }}
        </p>
        <p v-if="pausedWarning" class="text-sm text-[var(--ct-error)]">
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
import HandshakeIcon from '~icons/lucide/handshake'
import ShieldCheckIcon from '~icons/lucide/shield-check'
import Building2Icon from '~icons/lucide/building-2'
import UsersIcon from '~icons/lucide/users'
import {
  PLAN_TIERS,
  plan,
  planApi,
  loadPlan,
  describeChange,
  chosenExtras,
  chosenTier,
  getTierSpec,
  overLimitAfter,
  inGrace,
  openInvoice,
  dayAfterTrial,
} from './planApi'
import { Button, ErrorMessage, FormControl, toast } from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'

const { users } = usersStore()

const TIER_ICONS = {
  vendas: HandshakeIcon,
  credito_cobranca: ShieldCheckIcon,
  enterprise: Building2Icon,
}

const data = computed(() => plan.data)

const selectedTier = ref('credito_cobranca')
const selectedSpec = computed(() => getTierSpec(selectedTier.value))

// The plan the company pays for today ("Plano atual"); none during the trial.
const currentTier = computed(() => {
  const d = data.value
  if (!d || d.in_trial) return null
  if (['Active', 'Past Due'].includes(d.status)) return d.plan_tier || null
  if (d.status === 'Awaiting Payment') {
    return d.pending_plan_tier || d.plan_tier || null
  }
  return null
})

// Row text: the included-users line followed by the plan subtitle, both
// taken as-is from PLAN_TIERS (plan wording belongs to the owner).
function tierDescription(tier) {
  return `${tier.features[0]}. ${tier.subtitle}.`
}

const extrasDescription = computed(() => {
  const spec = selectedSpec.value
  if (!spec) return ''
  if (spec.unlimitedUsers) return `Usuários ilimitados no ${spec.name}.`
  const others = PLAN_TIERS.filter((t) => t.id !== spec.id).map((t) =>
    t.unlimitedUsers
      ? `ilimitados no ${t.name}`
      : `+ ${price(t.extraUserPrice)}/mês no ${t.name}`,
  )
  return `Além dos ${spec.includedUsers} inclusos no ${spec.name}. ${others.join(' · ')}.`
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

// Prices in the plan list read like the Figma: "R$ 119" (no cents when whole).
function price(value) {
  const v = value || 0
  return formatCurrency(
    v,
    null,
    data.value?.currency || 'BRL',
    Number.isInteger(v) ? 0 : 2,
  )
}

function money(value) {
  return formatCurrency(value || 0, null, data.value?.currency || 'BRL')
}

function date(value) {
  return formatDate(value, 'MMM D, YYYY')
}

onMounted(() => plan.loading || loadPlan())
</script>

<style scoped>
/* Figma plan icons: Lucide at 20px with a 1.4 stroke */
.ct-plan-icon :deep(path),
.ct-plan-icon :deep(circle),
.ct-plan-icon :deep(rect),
.ct-plan-icon :deep(line) {
  stroke-width: 1.4;
}
.ct-plan-icon {
  stroke-width: 1.4;
}
/* Stepper value: plain number, no browser spin buttons */
.ct-stepper-value {
  -moz-appearance: textfield;
  appearance: textfield;
}
.ct-stepper-value::-webkit-inner-spin-button,
.ct-stepper-value::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
