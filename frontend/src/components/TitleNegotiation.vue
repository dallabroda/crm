<template>
  <!-- Figma "Card · Títulos · Negociar (acordo) · preenchida" (2436:29107):
       564px modal, plain summary fields, Style Guide info alert, title history -->
  <Dialog v-model:open="open" :title="dialogTitle" :size="erpSource ? 'xl' : '3xl'">
    <template #default>
      <div v-if="title" class="ct-negotiation flex flex-col gap-3.5">
        <p class="text-p-base text-ink-gray-6">{{ dueLine }}</p>

        <!-- Resumo: quanto era, quanto já pagou e quanto falta (rótulo e valor, sem caixa) -->
        <div class="flex items-start gap-3">
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <span class="text-xs leading-4 text-ink-gray-6">{{ __('Original amount') }}</span>
            <span class="text-base font-medium leading-5 text-ink-gray-9">{{ money(title.original_amount) }}</span>
          </div>
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <span class="text-xs leading-4 text-ink-gray-6">{{ __('Paid') }}</span>
            <span class="text-base font-medium leading-5 text-[color:var(--ct-success)]">{{ money(title.paid_amount) }}</span>
          </div>
          <div class="flex min-w-0 flex-1 flex-col gap-1">
            <span class="text-xs leading-4 text-ink-gray-6">{{ __('Balance') }}</span>
            <span class="text-[16px] font-semibold leading-6 text-ink-gray-9">{{ money(balance) }}</span>
          </div>
        </div>

        <!-- Título do ERP: o saldo é do ERP (credtech#367); só promessa e acordo são feitos aqui.
             Style Guide "Aviso (toast)" Informação, sem botão e sem fechar -->
        <CtAlert v-if="erpSource" type="info" class="!items-center">
          {{
            __(
              'The balance of this title is controlled by {0}. Payments, settlements and installment agreements stay in the ERP; here you register the promise of payment.',
              [erpSource],
            )
          }}
        </CtAlert>

        <CtAlert v-if="registryWarning" type="warning" class="!items-center">
          {{ registryWarning }}
        </CtAlert>

        <!-- Pagamentos (só títulos sem ERP); a lista fica no histórico do título, abaixo -->
        <section v-if="!erpSource" class="flex flex-col gap-3.5">
          <h3 class="ct-section-title">{{ __('Payments') }}</h3>
          <div v-if="paid" class="text-p-base text-[color:var(--ct-success)]">
            {{ __('This title is fully paid.') }}
          </div>
          <div v-else class="ct-fields grid grid-cols-[1fr_1fr_2fr_auto] items-end gap-3">
            <FormControl v-model.number="payment.amount" type="number" :label="__('Amount (R$)')" />
            <FormControl v-model="payment.paid_on" type="date" format="DD/MM/YYYY" placeholder="dd/mm/aaaa" :label="__('Paid on')" :max="today" />
            <FormControl v-model="payment.note" type="text" :label="__('Note')" :placeholder="__('PIX, boleto, bank transfer...')" />
            <div class="pb-1">
              <Button
                variant="solid"
                size="lg"
                :label="__('Register payment')"
                :loading="busy === 'pay'"
                :disabled="!payment.amount || payment.amount <= 0 || Boolean(busy)"
                @click="registerPayment"
              />
            </div>
          </div>
        </section>

        <!-- Promessa de pagamento -->
        <section v-if="!paid" class="flex flex-col gap-3.5">
          <h3 class="ct-section-title">{{ __('Promise of payment') }}</h3>
          <div class="ct-fields grid grid-cols-[1fr_1fr_auto] items-end gap-3">
            <FormControl v-model="promise.date" type="date" format="DD/MM/YYYY" placeholder="dd/mm/aaaa" :label="__('Promised for')" :min="today" />
            <FormControl v-model.number="promise.amount" type="number" :label="__('Promised amount (R$)')" :placeholder="money(balance)" />
            <!-- Figma "Botão" Destaque 40px, centered on the 48px field -->
            <div class="pb-1">
              <Button
                variant="solid"
                size="lg"
                :label="__('Save promise')"
                :loading="busy === 'promise'"
                :disabled="!promise.date || Boolean(busy)"
                @click="savePromise"
              />
            </div>
          </div>
          <div v-if="promiseBroken" class="text-p-base text-[color:var(--ct-danger)]">
            {{ __('The promise of {0} was not kept.', [date(title.promise_date)]) }}
          </div>
        </section>

        <!-- Acordo: cronograma de parcelas -->
        <section v-if="(!paid && !erpSource) || installments.length" class="flex flex-col gap-3.5">
          <h3 class="ct-section-title">{{ __('Agreement') }}</h3>

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
            <div v-if="!builder.rows.length" class="ct-fields grid grid-cols-[1fr_1fr_auto] items-end gap-3">
              <FormControl v-model.number="builder.count" type="number" :label="__('Number of installments')" min="1" max="60" />
              <FormControl v-model="builder.first" type="date" format="DD/MM/YYYY" placeholder="dd/mm/aaaa" :label="__('First due date')" :min="today" />
              <div class="pb-1">
                <Button
                  variant="outline"
                  size="lg"
                  :label="__('Build schedule')"
                  :loading="busy === 'suggest'"
                  :disabled="!builder.count || !builder.first || Boolean(busy)"
                  @click="buildSchedule"
                />
              </div>
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
        <section v-if="!paid && !erpSource" class="flex flex-col gap-3.5">
          <h3 class="ct-section-title">{{ __('Adjust balance') }}</h3>
          <div class="ct-fields grid grid-cols-[1fr_2fr_auto] items-end gap-3">
            <FormControl v-model.number="adjust.balance" type="number" :label="__('New balance (R$)')" :placeholder="money(balance)" />
            <FormControl v-model="adjust.reason" type="text" :label="__('Reason')" :placeholder="__('Interest until today, discount agreed...')" />
            <div class="pb-1">
              <Button
                variant="outline"
                size="lg"
                :label="__('Save balance')"
                :loading="busy === 'adjust'"
                :disabled="!adjust.balance || adjust.balance <= 0 || Boolean(openInstallments.length) || Boolean(busy)"
                @click="adjustBalance"
              />
            </div>
          </div>
          <div v-if="openInstallments.length" class="text-xs text-ink-gray-5">
            {{ __('This title has an agreement in progress. Cancel the agreement before changing the balance.') }}
          </div>
        </section>

        <!-- Histórico do título: promessa e pagamentos, do mais novo ao mais antigo -->
        <section v-if="history.length" class="flex flex-col gap-2">
          <h3 class="ct-section-title">{{ __('Title history') }}</h3>
          <div
            v-for="item in history"
            :key="item.key"
            class="flex items-center gap-3 rounded-[var(--ct-radius-md)] bg-surface-gray-2 px-3 py-2"
            :title="item.note || ''"
          >
            <component :is="item.icon" class="size-4 shrink-0 text-ink-gray-9" aria-hidden="true" />
            <div class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="text-p-base font-medium text-ink-gray-9">{{ item.text }}</span>
              <span v-if="item.meta" class="text-xs leading-4 text-ink-gray-6">{{ item.meta }}</span>
            </div>
            <button
              v-if="item.action"
              type="button"
              class="shrink-0 text-p-base font-medium underline"
              :class="item.action.danger ? 'text-[color:var(--ct-danger)]' : 'text-ink-gray-9'"
              :disabled="Boolean(busy)"
              @click="item.action.run"
            >
              {{ item.action.label }}
            </button>
          </div>
        </section>
      </div>
    </template>
    <template #actions>
      <!-- Figma "Rodapé": outline "Fechar" on the right (the gray band is the Dialog's) -->
      <div class="flex justify-end">
        <Button variant="outline" :label="__('Close')" @click="open = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Badge, Button, Dialog, FormControl, call, toast } from 'frappe-ui'
import CalendarIcon from '~icons/lucide/calendar'
import CircleCheckIcon from '~icons/lucide/circle-check'
import CtAlert from '@/components/CtAlert.vue'
import { usersStore } from '@/stores/users'
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
// Linha abaixo do título: vencimento, atraso e valor atualizado (o mesmo da coluna da tabela)
const dueLine = computed(() => {
  const t = title.value
  if (!t?.due_date) return __('Updated amount {0}', [money(balance.value)])
  const late = Math.round((new Date(today) - new Date(String(t.due_date).slice(0, 10))) / 86400000)
  return late > 0
    ? __('Overdue since {0} ({1} days late) · updated amount {2}', [longDate(t.due_date), late, money(balance.value)])
    : __('Due on {0} · updated amount {1}', [longDate(t.due_date), money(balance.value)])
})

// Histórico do título: a promessa em vigor e os pagamentos, do mais novo ao mais antigo
const { getUser } = usersStore()
const history = computed(() => {
  const items = []
  const t = title.value
  if (t?.promise_date) {
    items.push({
      key: 'promise',
      icon: CalendarIcon,
      text: __('Promise of payment for {0} · {1}', [date(t.promise_date), money(t.promise_amount || balance.value)]),
      meta: '',
      action: { label: __('Clear'), run: clearPromise },
    })
  }
  for (const entry of [...payments.value].sort((a, b) => String(b.paid_on).localeCompare(String(a.paid_on)))) {
    const slot = entry.installment ? ` (${__('installment {0}', [installmentNumber(entry.installment)])})` : ''
    items.push({
      key: entry.name,
      icon: CircleCheckIcon,
      text: __('Payment of {0} · balance after {1}', [money(entry.amount), money(entry.balance_after)]) + slot,
      meta: [entry.registered_by ? getUser(entry.registered_by).full_name : '', date(entry.paid_on)].filter(Boolean).join(' · '),
      note: entry.note,
      action: erpSource.value ? null : { label: __('Reverse'), danger: true, run: () => confirmReverse(entry) },
    })
  }
  return items
})

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

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

// "21 out 2026", como no Figma
function longDate(value) {
  const [y, m, d] = String(value).slice(0, 10).split('-')
  return `${d} ${MONTHS[Number(m) - 1]} ${y}`
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

<style scoped>
/* Figma section title: 14 Semi Bold, Uso/Texto/Principal */
.ct-section-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  color: var(--ct-text-primary);
}
/* Figma "Campo" (940:99): 14 Medium gray label, 6px gap, white 48px box with
   the #dcdde2 border, 6px radius, 16px value */
.ct-fields :deep(label) {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  color: var(--ct-text-secondary);
}
.ct-fields :deep(input) {
  height: 48px;
  padding-inline: 14px;
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-radius-sm);
  background: var(--ct-bg-page);
  font-size: 16px;
  line-height: 24px;
  color: var(--ct-text-primary);
}
.ct-fields :deep(input:focus) {
  border-color: var(--ct-border-strong);
  box-shadow: 0 0 0 1px var(--ct-border-strong);
}
</style>
