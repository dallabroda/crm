<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Lead Sources')">
      <template #description>
        {{
          __(
            'Leads from your ads and forms land in the funnel within seconds, already assigned to a salesperson.',
          )
        }}
      </template>
    </SettingsPageHeader>
    <div class="flex flex-1 flex-col gap-8 overflow-y-auto px-2">
      <MetaLeadsSource @changed="activity?.load()" />
      <WebhookSources @changed="activity?.load()" />
      <ChatConnection />
      <EmailCompanySetting />
      <LeadActivity ref="activity" />
    </div>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
// Lead sources connected by the company admin (credtech#51). The old screen,
// where a Meta access token was pasted by hand, gave way to "Connect with
// Facebook": the token never shows up here.
import MetaLeadsSource from './MetaLeadsSource.vue'
import WebhookSources from './WebhookSources.vue'
import ChatConnection from './ChatConnection.vue'
import EmailCompanySetting from './EmailCompanySetting.vue'
import LeadActivity from './LeadActivity.vue'
import { ref } from 'vue'

const activity = ref(null)
</script>
