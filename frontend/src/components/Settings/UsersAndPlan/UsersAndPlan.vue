<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Users and Plan') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Your plan includes {0} free users. Each extra user costs {1} per month, paid by card.',
              [data?.free ?? 2, money(data?.price_per_user)],
            )
          }}
        </p>
      </div>
    </div>

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
      class="mx-2 rounded border border-outline-gray-1 px-4 py-3 text-p-base text-ink-gray-7"
    >
      {{ __('Your company has no user limit.') }}
    </div>

    <div v-else class="flex flex-col gap-6 overflow-y-auto px-2">
      <!-- Usage and status -->
      <div class="flex flex-col gap-3 rounded border border-outline-gray-1 p-4">
        <div class="flex items-center justify-between gap-4">
          <div class="flex flex-col gap-0.5">
            <span class="text-lg-semibold text-ink-gray-8">
              {{ __('{0} of {1} users', [seats.used, seats.limit]) }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __('{0} active, {1} invited', [
                  data.used_active,
                  data.used_invited,
                ])
              }}
            </span>
          </div>
          <Badge
            :label="statusBadge(data.status).label"
            :theme="statusBadge(data.status).theme"
            variant="subtle"
            size="lg"
          />
        </div>
        <div
          class="h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3"
        >
          <div
            class="h-full rounded-full"
            :class="seats.full ? 'bg-surface-red-5' : 'bg-surface-gray-7'"
            :style="{ width: barWidth }"
          />
        </div>
        <p
          v-if="seats.full && data.status !== 'Awaiting Payment'"
          class="text-p-sm text-ink-gray-6"
        >
          {{
            __(
              'All seats are in use. To invite someone else, contract extra users below.',
            )
          }}
        </p>
        <div
          v-if="data.status === 'Active' && data.next_due && data.amount"
          class="text-p-sm text-ink-gray-6"
        >
          {{
            __('Next charge: {0} on {1}', [
              money(data.amount),
              date(data.next_due),
            ])
          }}
        </div>
      </div>

      <!-- What needs attention -->
      <PlanNotice
        v-if="data.status === 'Awaiting Payment'"
        theme="orange"
        :text="
          __(
            'Waiting for the first payment. The {0} extra users are released as soon as it is confirmed.',
            [data.pending_extras],
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
        <div class="text-base-semibold">{{ __('Paused by the plan') }}</div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Their data is kept. They come back on their own when there is a seat again.',
            )
          }}
        </p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="user in data.paused_users"
            :key="user.name"
            class="flex items-center gap-2 rounded-6 bg-surface-gray-2 px-2 py-1 text-base"
          >
            <span class="text-ink-gray-8">{{
              user.full_name || user.name
            }}</span>
            <span class="text-ink-gray-5">{{ user.name }}</span>
          </li>
        </ul>
      </div>

      <!-- Change the number of extra users -->
      <div class="flex flex-col gap-4 border-t border-outline-gray-1 pt-6">
        <div class="text-base-semibold">{{ __('Extra users') }}</div>
        <div class="flex items-center gap-3">
          <FormControl
            v-model="quantity"
            type="number"
            class="w-40"
            :min="0"
            :max="500"
            :disabled="saving"
          />
          <span class="text-p-base text-ink-gray-7">
            {{
              __('{0} users in total, {1} per month', [
                (data.free || 0) + extras,
                money(change.monthly),
              ])
            }}
          </span>
        </div>
        <ErrorMessage v-if="errors.quantity" :message="errors.quantity" />

        <p v-if="explanation" class="text-p-sm text-ink-gray-6">
          {{ explanation }}
        </p>
        <p v-if="pausedWarning" class="text-p-sm text-ink-red-4">
          {{ pausedWarning }}
        </p>

        <template v-if="askPayer">
          <div class="flex flex-col gap-0.5">
            <div class="text-base-semibold">{{ __('Who pays') }}</div>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Used for the invoice. The card is typed on the payment page, never in Cred Hub.',
                )
              }}
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3">
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
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { formatCurrency } from '@/utils/numberFormat'
import PlanNotice from './PlanNotice.vue'
import {
  plan,
  planApi,
  loadPlan,
  usage,
  describeChange,
  chosenExtras,
  overLimitAfter,
  statusBadge,
  inGrace,
  openInvoice,
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

const quantity = ref(0)
const extras = computed(() => Math.max(0, parseInt(quantity.value, 10) || 0))
const change = computed(() => describeChange(data.value, extras.value))
const saving = ref(false)
const errors = reactive({})

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
    subscribe: __(
      'You pay the first month on the payment page. The extra users are released as soon as the payment is confirmed. Then {0} per month on the same card.',
      [monthly],
    ),
    increase: __(
      'The new users are released now. The prorated difference until {0} goes by payment link, with 3 days to pay. Then {1} per month.',
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
      'Keeps the extra users already paid and drops the pending change.',
    ),
    free: __('Back to the {0} free users, with no charges.', [
      data.value?.free,
    ]),
  }[change.value.kind]
})

const pausedWarning = computed(() => {
  const kind = change.value.kind
  if (!['decrease', 'cancel', 'free'].includes(kind)) return null
  const over = overLimitAfter(data.value, extras.value)
  if (!over) return null
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

watch(data, (value) => (quantity.value = chosenExtras(value)), {
  immediate: true,
})

async function save() {
  Object.keys(errors).forEach((key) => delete errors[key])
  saving.value = true
  try {
    const result = await planApi.requestExtraUsers(
      extras.value,
      askPayer.value ? { ...payer } : null,
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
  return formatDate(value, null, true)
}

onMounted(loadPlan)
</script>
