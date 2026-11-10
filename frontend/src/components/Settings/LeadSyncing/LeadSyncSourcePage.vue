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
      <!-- Figma: "Adicionar origem" sits in the top bar; the options come
           from the "Google Ads, website and other tools" card -->
      <template #actions>
        <Dropdown :options="webhooks?.addOptions || []" align="end">
          <Button
            variant="solid"
            :label="__('Add source')"
            icon-left="lucide-plus"
            :loading="webhooks?.creating"
          />
        </Dropdown>
      </template>
    </SettingsPageHeader>
    <!-- Figma "Configurações · Origens" (882:2): one bordered card per
         source (8px radius, 20px padding), 24px apart -->
    <div class="ct-sources flex flex-1 flex-col gap-6 overflow-y-auto">
      <MetaLeadsSource @changed="activity?.load()" />
      <WebhookSources ref="webhooks" @changed="activity?.load()" />
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
import { Button, Dropdown } from 'frappe-ui'
import { ref } from 'vue'

const activity = ref(null)
const webhooks = ref(null)
</script>

<style scoped>
.ct-sources > :deep(.rounded-lg.border) {
  border-radius: var(--ct-radius-md);
  border-color: var(--ct-border);
  padding: 20px;
}
/* card titles 14/500, descriptions 14 gray */
.ct-sources > :deep(.rounded-lg.border .text-base-semibold) {
  font-weight: 500;
}
.ct-sources > :deep(.rounded-lg.border .text-p-sm) {
  font-size: 14px;
  line-height: 20px;
}
</style>
