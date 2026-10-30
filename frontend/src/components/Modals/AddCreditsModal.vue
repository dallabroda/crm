<template>
  <Dialog v-model:open="show" :title="__('Add Premium Bureau Credits')" :size="'md'">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'Prepaid balance used to pay for Boa Vista, Dossiê QUOD and SCR Bacen queries. You will be redirected to a payment page.',
            )
          }}
        </p>
        <FormControl
          v-model.number="amount"
          type="number"
          :label="__('Amount (R$)')"
          :placeholder="String(minTopup)"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Continue to Payment')"
          :loading="sending"
          :disabled="!amount || amount < minTopup"
          @click="send"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, FormControl, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  minTopup: { type: Number, default: 10 },
})
const emit = defineEmits(['topup-requested'])
const show = defineModel({ type: Boolean })

const amount = ref(props.minTopup)
const sending = ref(false)
const error = ref('')

watch(show, (open) => {
  if (!open) return
  amount.value = props.minTopup
  error.value = ''
})

async function send() {
  sending.value = true
  error.value = ''
  try {
    const res = await call('cred_hub.billing.request_credit_topup', {
      amount: amount.value,
    })
    if (res?.ok === false) {
      error.value = res.message || __('Could not start the payment.')
      return
    }
    if (res?.invoice_url) {
      window.open(res.invoice_url, '_blank')
      toast.success(__('Payment page opened in a new tab. Credits are added once it is confirmed.'))
      emit('topup-requested')
      show.value = false
    }
  } catch (err) {
    error.value = err?.messages?.[0] || err?.message || __('Something went wrong')
  } finally {
    sending.value = false
  }
}
</script>
