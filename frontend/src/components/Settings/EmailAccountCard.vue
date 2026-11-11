<template>
  <!-- Figma "E-mail · Contas · preenchida" (2336:10121), "Linha": account,
       provider, usage pills and Editar; 10px/16px padding, 16px apart -->
  <div
    class="flex cursor-pointer items-center gap-4 px-4 py-2.5 hover:bg-surface-gray-2"
  >
    <div class="flex min-w-0 flex-1 flex-col">
      <div class="truncate text-[14px] font-medium leading-5 text-ink-gray-9">
        {{ emailAccount.email_account_name }}
      </div>
      <div class="truncate text-xs text-[var(--ct-text-tertiary)]">
        {{ emailAccount.email_id }}
      </div>
    </div>
    <div
      class="w-[152px] shrink-0 truncate text-[14px] leading-5 text-ink-gray-6"
    >
      {{ providerLabel }}
    </div>
    <div class="flex w-[335px] shrink-0 flex-wrap items-center gap-2">
      <span
        v-for="label in usage"
        :key="label"
        class="rounded-full bg-[var(--ct-bg-panel)] px-2.5 py-0.5 text-xs font-medium text-ink-gray-9"
      >
        {{ label }}
      </span>
    </div>
    <div class="w-[105px] shrink-0">
      <Button :label="__('Edit')" variant="outline" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  emailAccount: { type: Object, required: true },
})

// Figma writes the providers as people know them ("Gmail")
const providerLabel = computed(() =>
  props.emailAccount.service === 'GMail' ? 'Gmail' : props.emailAccount.service,
)

// "Uso": what the account is the default for, and whether it receives
const usage = computed(() => {
  const account = props.emailAccount
  const labels = []
  if (account.default_outgoing) labels.push(__('Default for sending'))
  if (account.default_incoming) labels.push(__('Default for receiving'))
  if (account.enable_incoming) labels.push(__('Receives emails'))
  return labels
})
</script>
