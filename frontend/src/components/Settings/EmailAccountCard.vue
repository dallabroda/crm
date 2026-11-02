<template>
  <div
    class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-surface-gray-2"
  >
    <!-- avatar and name -->
    <div class="flex items-center justify-between gap-2">
      <EmailProviderIcon :logo="emailIcon[emailAccount.service]" />
      <div>
        <div class="text-base font-medium text-ink-gray-9">
          {{ emailAccount.email_account_name }}
        </div>
        <div class="text-base text-ink-gray-6">
          {{ emailAccount.email_id }}
        </div>
      </div>
    </div>
    <div>
      <Badge variant="subtle" :label="badgeTitle" theme="gray" />
    </div>
    <!-- email id -->
  </div>
</template>

<script setup>
import { emailIcon } from './emailConfig'
import EmailProviderIcon from './EmailProviderIcon.vue'
import { computed } from 'vue'

const props = defineProps({
  emailAccount: { type: Object, required: true },
})

const badgeTitle = computed(() => {
  if (
    props.emailAccount.default_incoming &&
    props.emailAccount.default_outgoing
  ) {
    return __('Default Sending & Inbox')
  } else if (props.emailAccount.default_incoming) {
    return __('Default Inbox')
  } else if (props.emailAccount.default_outgoing) {
    return __('Default Sending')
  } else {
    return __('Inbox')
  }
})
</script>

<style scoped></style>
