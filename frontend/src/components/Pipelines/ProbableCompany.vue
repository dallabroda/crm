<template>
  <div
    v-if="deal?.email_company_status === 'Suggested'"
    class="flex flex-col gap-2 border-b bg-surface-gray-1 px-4 py-3"
    data-testid="probable-company"
  >
    <div class="text-base-medium text-ink-gray-8">
      {{ __('Probable company') }}
    </div>
    <p class="text-p-sm text-ink-gray-7">
      {{
        __('{0} (CNPJ {1}), from the e-mail domain {2}.', [
          deal.email_company_name,
          deal.email_company_cnpj,
          deal.email_company_domain,
        ])
      }}
    </p>
    <div class="flex gap-2">
      <Button
        variant="solid"
        :label="__('Confirm')"
        :loading="busy === 'confirm'"
        @click="run('confirm')"
      />
      <Button
        :label="__('Dismiss')"
        :loading="busy === 'dismiss'"
        @click="run('dismiss')"
      />
    </div>
  </div>
</template>

<script setup>
// Company found from the lead's e-mail domain with medium confidence
// (credtech#187): one click makes it the card's organization
import { call, toast } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  // the card (doc of useDocument)
  deal: { type: Object, default: null },
})
const emit = defineEmits(['changed'])
const busy = ref('')

async function run(action) {
  busy.value = action
  try {
    await call(`cred_hub.email_company.apply.${action}`, {
      deal: props.deal.name,
    })
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the choice'))
  } finally {
    busy.value = ''
  }
}
</script>
