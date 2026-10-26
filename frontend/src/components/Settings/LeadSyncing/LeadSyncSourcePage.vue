<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2 pt-2">
      <h2 class="flex h-5 text-2xl-semibold leading-none">
        {{ __('Lead Sources') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Leads from your ads and forms land in the funnel within seconds, already assigned to a salesperson.',
          )
        }}
      </p>
    </div>
    <div class="flex flex-1 flex-col gap-8 overflow-y-auto px-2">
      <MetaLeadsSource @changed="activity?.load()" />
      <WebhookSources @changed="activity?.load()" />
      <ChatConnection />
      <LeadActivity ref="activity" />
    </div>
  </div>
</template>

<script setup>
// Lead sources connected by the company admin (credtech#51). The old screen,
// where a Meta access token was pasted by hand, gave way to "Connect with
// Facebook": the token never shows up here.
import MetaLeadsSource from './MetaLeadsSource.vue'
import WebhookSources from './WebhookSources.vue'
import ChatConnection from './ChatConnection.vue'
import LeadActivity from './LeadActivity.vue'
import { ref } from 'vue'

const activity = ref(null)
</script>
