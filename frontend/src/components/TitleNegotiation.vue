<template>
  <Dialog v-model:open="open" :title="dialogTitle" size="3xl">
    <template #default>
      <div v-if="title" class="flex flex-col gap-6 py-1">
        <!-- Resumo: quanto era, quanto já pagou e quanto falta -->
        <div class="grid grid-cols-3 gap-3">
          <div class="rounded border border-outline-gray-2 p-3">
            <div class="text-xs text-ink-gray-5">{{ __('Original amount') }}</div>
            <div class="text-base font-medium text-ink-gray-8">{{ money(title.original_amount) }}</div>
          </div>
          <div class="rounded border border-outline-gray-2 p-3">
            <div class="text-xs text-ink-gray-5">{{ __('Paid') }}</div>
            <div class="text-base font-medium text-ink-green-3">{{ money(title.paid_amount) }}</div>
          </div>
          <div class="rounded border border-outline-gray-2 p-3">
            <div class="text-xs text-ink-gray-5">{{ __('Balance') }}</div>
            <div class="text-base font-semibold text-ink-gray-9">{{ money(balance) }}</div>
          </div>
        </div>

        <!-- Título do ERP: o saldo é do ERP (credtech#367); só promessa e acordo são feitos aqui -->
        <div
          v-if="erpSource"
          class="rounded-lg bg-[#E5F1FF] px-4 py-3 text-base leading-5 text-[#1E1F23]"
        >
          {{
            __(
              'The balance of this title is controlled by {0}. Payments, settlements and installment agreements stay in the ERP; here you register the promise of payment.',
              [erpSource],
            )
          }}
        </div>

        <div
          v-if="registryWarning"
          class="rounded border border-outline-amber-2 bg-surface-amber-1 p-3 text-sm text-[color:var(--ct-warning)] font-medium"
        >
          {{ registryWarning }}
        </div>

        <!-- Pagamentos -->
        <section class="flex flex-col gap-3">
          <h3 class="text-base font-semibold text-ink-gray-8">{{ __('Payments') }}</h3>
          <div v-if="paid" class="text-sm text-ink-green-3">
            {{ __('This title is fully paid.') }}
          </div>
          <div v-else-if="!erpSource" class="grid grid-cols-[1fr_1fr_2fr_auto] items-end gap-3">
            <FormControl v-model.number="payment.amount" type="number" :label="__('Amount (R$)')" />
            <FormControl v-model="payment.paid_on" type="date" :label="__('Paid on')" :max="today" />
            <FormControl v-model="payment.note" type="text" :label="__('Note')" :placeholder="__('PIX, boleto, bank transfer...')" />
            <Button
              variant="solid"
              :label="__('Register payment')"
              :loading="busy === 'pay'"
              :disabled="!payment.amount || payment.amount <= 0 || Boolean(busy)"
              @click="registerPayment"
            />
          </div>
          <table v-if="payments.length" class="w-full text-left text-p-sm">
            <thead>
              <tr class="border-b border-outline-gray-2 text-ink-gray-5">
                <th class="py-2 pr-3">{{ __('Paid on') }}</th>
                <th class="py-2 pr-3 text-right">{{ __('Amount') }}</th>
                <th class="py-2 pr-3 text-right">{{ __('Balance after') }}</th>
                <th class="py-2 pr-3">{{ __('Note') }}</th>
                <th class="py-2 pr-3">{{ __('Registered by') }}</th>
                <th class="py-2"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-1">
              <tr v-for="entry in payments" :key="entry.name">
                <td class="py-2 pr-3">{{ date(entry.paid_on) }}</td>
                <td class="py-2 pr-3 text-right font-medium">{{ money(entry.amount) }}</td>
                <td class="py-2 pr-3 text-right text-ink-gray-6">{{ money(entry.balance_after) }}</td>
                <td class="py-2 pr-3 text-ink-gray-7">
                  {{ entry.note || '—' }}
                  <span v-if="entry.installment" class="text-xs text-ink-gray-5">
                    ({{ __('installment {0}', [installmentNumber(entry.installment)]) }})
                  </span>
                </td>
                <td class="py-2 pr-3 text-ink-gray-6">{{ entry.registered_by }}</td>
                <td class="py-2 text-right">
                  <button
                    v-if="!erpSource"
                    type="button"
                    class="text-xs text-ink-red-4 hover:underline"
                    :disabled="Boolean(busy)"
                    @click="confirmReverse(entry)"
                  >
                    {{ __('Reverse') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-sm text-ink-gray-5">{{ __('No payment registered yet.') }}</div>
        </section>

        <!-- Promessa de pagamento -->
        <section v-if="!paid" class="flex flex-col gap-3">
          <h3 class="text-base font-semibold text-ink-gray-8">{{ __('Promise of payment') }}</h3>
          <div class="grid grid-cols-[1fr_1fr_auto_auto] items-end gap-3">
            <FormControl v-model="promise.date" type="date" :label="__('Promised for')" :min="today" />
            <FormControl v-model.number="promise.amount" type="number" :label="__('Promised amount (R$)')" :placeholder="money(balance)" />
            <Button
              :label="__('Save promise')"
              :loading="busy === 'promise'"
              :disabled="!promise.date || Boolean(busy)"
              @click="savePromise"
            />
            <Button
              v-if="title.promise_date"
              :label="__('Clear')"
              :disabled="Boolean(busy)"
              @click="clearPromise"
            />
          </div>
          <div v-if="promiseBroken" class="text-sm text-ink-red-4">
            {{ __('The promise of {0} was not kept.', [date(title.promise_date)]) }}
          </div>
        </section>

        <!-- Acordo: cronograma de parcelas -->
        <section v-if="(!paid && !erpSource) || installments.length" class="flex flex-col gap-3">
          <h3 class="text-base font-semibold text-ink-gray-8">{{ __('Agreement') }}</h3>

          <template v-if="installments.length">
            <table class="w-full text-left text-p-sm">
              <thead>
                <tr class="border-b border-outline-gray-2 text-ink-gray-5">
                  <th class="py-2 pr-3">#</th>
                  <th class="py-2 pr-3">{{ __('Due date') }}</th>
                  <th class="py-2 pr-3 text-right">{{ __('Amount') }}</th>
                  <th class="py-2 pr-3">{{ __('Status') }}</th>
                  <th class="py-2"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1">
                <tr v-for="slot in installments" :key="slot.name">
                  <td class="py-2 pr-3">{{ slot.number }}</td>
                  <td class="py-2 pr-3">{{ date(slot.due_date) }}</td>
                  <td class="py-2 pr-3 text-right font-medium">{{ money(slot.amount) }}</td>
                  <td class="py-2 pr-3">
                    <Badge v-if="slot.paid_on" :label="__('Paid on {0}', [date(slot.paid_on)])" theme="green" variant="subtle" />
                    <Badge v-else-if="slot.cancelled_on" :label="__('Cancelled on {0}', [date(slot.cancelled_on)])" theme="gray" variant="subtle" />
                    <Badge v-else-if="slot.due_date < today" :label="__('Overdue')" theme="red" variant="subtle" />
                    <Badge v-else :label="__('Open')" theme="gray" variant="subtle" />
                  </td>
                  <td class="py-2 text-right">
                    <Button
                      v-if="!slot.paid_on && !slot.cancelled_on && !erpSource"
                      size="sm"
                      :label="__('Mark as paid')"
                      :disabled="Boolean(busy)"
                      @click="payInstallment(slot)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="openInstallments.length">
              <Button
                variant="subtle"
                theme="red"
                :label="__('Cancel agreement')"
                :disabled="Boolean(busy)"
                @click="confirmCancelAgreement"
              />
            </div>
          </template>

          <!-- Novo acordo: só sem parcelas em aberto (o histórico de um acordo cancelado fica acima) e fora do ERP -->
          <template v-if="!openInstallments.length && !paid && !erpSource">
            <div v-if="!builder.rows.length" class="grid grid-cols-[1fr_1fr_auto] items-end gap-3">
              <FormControl v-model.number="builder.count" type="number" :label="__('Number of installments')" min="1" max="60" />
              <FormControl v-model="builder.first" type="date" :label="__('First due date')" :min="today" />
              <Button
                :label="__('Build schedule')"
                :loading="busy === 'suggest'"
                :disabled="!builder.count || !builder.first || Boolean(busy)"
                @click="buildSchedule"
              />
            </div>
            <template v-else>
              <div class="flex flex-col gap-2">
                <div v-for="(row, index) in builder.rows" :key="index" class="grid grid-cols-[2rem_1fr_1fr] items-center gap-3">
                  <span class="text-sm text-ink-gray-6">{{ index + 1 }}</span>
                  <FormControl v-model="row.due_date" type="date" :min="today" />
                  <FormControl v-model.number="row.amount" type="number" />
                </div>
              </div>
              <div class="text-sm" :class="scheduleMatches ? 'text-ink-green-3' : 'text-ink-red-4'">
                {{ __('Installments: {0}. Balance: {1}.', [money(scheduleTotal), money(balance)]) }}
                <span v-if="!scheduleMatches">
                  {{ __('They must add up to the balance. For a discount or interest, adjust the balance first.') }}
                </span>
              </div>
              <div class="flex gap-2">
                <Button
                  variant="solid"
                  :label="__('Create agreement')"
                  :loading="busy === 'agreement'"
                  :disabled="!scheduleMatches || Boolean(busy)"
                  @click="createAgreement"
                />
                <Button :label="__('Start over')" :disabled="Boolean(busy)" @click="builder.rows = []" />
              </div>
            </template>
          </template>
        </section>

        <!-- Ajuste de saldo (juros, desconto): fica no histórico do card -->
        <section v-if="!paid && !erpSource" class="flex flex-col gap-3">
          <h3 class="text-base font-semibold text-ink-gray-8">{{ __('Adjust balance') }}</h3>
          <div class="grid grid-cols-[1fr_2fr_auto] items-end gap-3">
            <FormControl v-model.number="adjust.balance" type="number" :label="__('New balance (R$)')" :placeholder="money(balance)" />
            <FormControl v-model="adjust.reason" type="text" :label="__('Reason')" :placeholder="__('Interest until today, discount agreed...')" />
            <Button
              :label="__('Save balance')"
              :loading="busy === 'adjust'"
              :disabled="!adjust.balance || adjust.balance <= 0 || Boolean(openInstallments.length) || Boolean(busy)"
              @click="adjustBalance"
            />
          </div>
          <div v-if="openInstallments.length" class="text-xs text-ink-gray-5">
            {{ __('This title has an agreement in progress. Cancel the agreement before changing the balance.') }}
          </div>
        </section>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button :label="__('Close')" @click="open = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Badge, Button, Dialog, FormControl, call, toast } from 'frappe-ui'
import { createDialog } from '@/utils/dialogs'

const props = defineProps({
  deal: { type: Object, required: true },
  titleName: { type: String, default: '' },
})
const open = defineModel('open', { type: Boolean, default: false })
const emit = defineEmits(['reload'])

const API = 'crm.api.collection.'
// Mesmos status em que o título pode estar no cartório: avisa, mas quem decide a retirada é o operador
const WITH_REGISTRY = ['COLETADO', 'GERADO', 'AGENDADO', 'ENVIADO', 'CONFIRMADO', 'DISTRIBUIDO', 'INTIMADO', 'PROTESTADO', 'SUSPENSO', 'SUSTADO']

const today = new Date().toLocaleDateString('sv-SE')
const busy = ref('')
const registryWarning = ref('')

const title = computed(() => (props.deal.titles || []).find((t) => t.name === props.titleName))
const payments = computed(() =>
  (props.deal.payments || []).filter((p) => p.title === props.titleName),
)
const installments = computed(() =>
  (props.deal.installments || [])
    .filter((i) => i.title === props.titleName)
    .sort((a, b) => a.number - b.number),
)
const openInstallments = computed(() => installments.value.filter((i) => !i.paid_on && !i.cancelled_on))

// Título que veio de um ERP (credtech#367): pagamento, estorno e ajuste de saldo só pela sincronização
const erpSource = computed(() => (title.value?.erp_title_id ? title.value.erp_source || 'ERP' : ''))

// Saldo: o valor atualizado é o que ainda se deve; título quitado fica com 0 (não volta ao original)
const balance = computed(() => {
  const t = title.value
  if (!t) return 0
  if (t.closed_reason) return 0
  const updated = Number(t.updated_amount || 0)
  return updated || Number(t.paid_amount || 0) ? updated : Number(t.original_amount || 0)
})
const paid = computed(() => balance.value <= 0.005)
const promiseBroken = computed(
  () => Boolean(title.value?.promise_date) && title.value.promise_date < today && !paid.value,
)
const dialogTitle = computed(() =>
  title.value ? __('Negotiation of title {0}', [title.value.title_number]) : __('Negotiation'),
)

const payment = reactive({ amount: null, paid_on: today, note: '' })
const promise = reactive({ date: '', amount: null })
const adjust = reactive({ balance: null, reason: '' })
const builder = reactive({ count: 3, first: '', rows: [] })

const scheduleTotal = computed(() =>
  builder.rows.reduce((sum, r) => sum + Number(r.amount || 0), 0),
)
const scheduleMatches = computed(
  () => builder.rows.length > 0 && Math.abs(scheduleTotal.value - balance.value) < 0.005,
)

function money(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value || 0))
}

function date(value) {
  if (!value) return '—'
  const [y, m, d] = String(value).slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

function installmentNumber(name) {
  return installments.value.find((i) => i.name === name)?.number ?? '?'
}

function resetForms() {
  payment.amount = null
  payment.paid_on = today
  payment.note = ''
  promise.date = title.value?.promise_date || ''
  promise.amount = title.value?.promise_amount || null
  adjust.balance = null
  adjust.reason = ''
  builder.rows = []
  registryWarning.value = ''
  const t = title.value
  if (t && WITH_REGISTRY.includes((t.protest_status || '').toUpperCase()) && t.sent_at) {
    registryWarning.value = __(
      'This title is with the registry ({0}). Withdrawing or cancelling it is your decision and may have a cost.',
      [(t.protest_status || '').toUpperCase()],
    )
  }
}

watch(open, (value) => value && resetForms())

// Chama a API, avisa o resultado e recarrega o card para a tabela mostrar o saldo novo
async function run(key, method, args, done) {
  busy.value = key
  try {
    const res = await call(API + method, { deal: props.deal.name, ...args })
    if (res?.warning) registryWarning.value = res.warning
    if (done) toast.success(done)
    emit('reload', { reloadDoc: true })
    return res
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Could not save.'))
    return null
  } finally {
    busy.value = ''
  }
}

async function registerPayment() {
  const res = await run(
    'pay',
    'record_payment',
    { title: props.titleName, amount: payment.amount, paid_on: payment.paid_on, note: payment.note },
    __('Payment registered.'),
  )
  if (!res) return
  payment.amount = null
  payment.note = ''
  if (res.all_paid) {
    toast.info(__('Every title of this card is paid. Mark the card as Won when you are ready.'))
  }
}

async function payInstallment(slot) {
  await run(
    'pay',
    'record_payment',
    { title: props.titleName, installment: slot.name, paid_on: today },
    __('Installment {0} paid.', [slot.number]),
  )
}

function confirmReverse(entry) {
  createDialog({
    title: __('Reverse payment'),
    message: __('The {0} of {1} goes back to the balance of the title.', [money(entry.amount), date(entry.paid_on)]),
    size: 'md',
    actions: [
      { label: __('Back'), onClick: ({ close }) => close() },
      {
        label: __('Reverse'),
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }) => {
          close()
          run('reverse', 'reverse_payment', { payment: entry.name }, __('Payment reversed.'))
        },
      },
    ],
  })
}

async function savePromise() {
  await run(
    'promise',
    'set_promise',
    { title: props.titleName, promise_date: promise.date, promise_amount: promise.amount || null },
    __('Promise saved.'),
  )
}

async function clearPromise() {
  const res = await run('promise', 'set_promise', { title: props.titleName }, __('Promise cleared.'))
  if (res) {
    promise.date = ''
    promise.amount = null
  }
}

async function adjustBalance() {
  const res = await run(
    'adjust',
    'adjust_balance',
    { title: props.titleName, balance: adjust.balance, reason: adjust.reason },
    __('Balance updated.'),
  )
  if (res) {
    adjust.balance = null
    adjust.reason = ''
  }
}

// O sistema sugere parcelas mensais iguais; o analista ajusta datas e valores antes de criar
async function buildSchedule() {
  busy.value = 'suggest'
  try {
    builder.rows = await call(API + 'suggest_agreement', {
      deal: props.deal.name,
      title: props.titleName,
      count: builder.count,
      first_due: builder.first,
    })
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Could not build the schedule.'))
  } finally {
    busy.value = ''
  }
}

async function createAgreement() {
  const res = await run(
    'agreement',
    'create_agreement',
    { title: props.titleName, installments: JSON.stringify(builder.rows) },
    __('Agreement created.'),
  )
  if (res) builder.rows = []
}

function confirmCancelAgreement() {
  createDialog({
    title: __('Cancel agreement'),
    message: __('The open installments are marked as cancelled. The whole agreement stays in the history.'),
    size: 'md',
    actions: [
      { label: __('Back'), onClick: ({ close }) => close() },
      {
        label: __('Cancel agreement'),
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }) => {
          close()
          run('agreement', 'cancel_agreement', { title: props.titleName }, __('Agreement cancelled.'))
        },
      },
    ],
  })
}
</script>
