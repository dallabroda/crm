<template>
  <div class="flex h-full flex-col gap-6">
    <!-- Figma "E-mail · Contas" (2336:10121): one "E-mail" page, tabs Contas
         and Modelos, then the description and the table -->
    <SettingsSectionTabs :tabs="emailTabs" active="email-accounts" />
    <SettingsPageHeader :title="__('Email')">
      <template #description>
        {{
          __(
            'Connect email accounts to send and receive emails from CRM. Set one as the default for incoming and outgoing emails.',
          )
        }}
      </template>
      <template #actions>
        <Button
          :label="__('Add Account')"
          theme="gray"
          variant="solid"
          icon-left="lucide-plus"
          @click="emit('update:step', 'email-add')"
        />
      </template>
    </SettingsPageHeader>

    <!-- list accounts: Figma "Tabela" (8px radius, 40px gray header) -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="overflow-hidden rounded-lg border border-[var(--ct-border)]"
    >
      <div
        class="flex h-10 items-center gap-4 border-b border-[var(--ct-border)] bg-[var(--ct-bg-soft)] px-4 text-xs font-medium text-ink-gray-6"
      >
        <div class="min-w-0 flex-1">{{ __('Account') }}</div>
        <div class="w-[152px] shrink-0">{{ __('Provider') }}</div>
        <div class="w-[335px] shrink-0">{{ __('Usage') }}</div>
        <div class="w-[105px] shrink-0" />
      </div>
      <EmailAccountCard
        v-for="emailAccount in emailAccounts.data"
        :key="emailAccount.name"
        class="border-b border-[var(--ct-border)] last:border-b-0"
        :emailAccount="emailAccount"
        @click="emit('update:step', 'email-edit', emailAccount)"
      />
    </div>
    <!-- fallback if no email accounts -->
    <SettingsEmptyState
      v-else
      :icon="LucideMail"
      :title="__('No email account connected')"
      :description="
        __('Connect an account to send and receive emails from the CRM.')
      "
      :action-label="__('Add Account')"
      @action="emit('update:step', 'email-add')"
    />
  </div>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsSectionTabs from '@/components/Settings/SettingsSectionTabs.vue'
import EmailAccountCard from './EmailAccountCard.vue'
import { emailTabs, getSystemEmailAccounts } from './emailConfig'
import { createListResource } from 'frappe-ui'

const emit = defineEmits(['update:step'])

// Always read from the server: a cached copy showed stale switches (credtech#191)
const emailAccounts = createListResource({
  doctype: 'Email Account',
  fields: ['*'],
  filters: {
    email_id: ['Not Like', '%example%'],
  },
  pageLength: 10,
  auto: false,
  onSuccess: (accounts) => {
    // convert 0 to false to handle boolean fields
    accounts.forEach((account) => {
      account.enable_incoming = Boolean(account.enable_incoming)
      account.enable_outgoing = Boolean(account.enable_outgoing)
      account.default_incoming = Boolean(account.default_incoming)
      account.default_outgoing = Boolean(account.default_outgoing)
      account.create_lead_from_incoming_email = Boolean(
        account.create_lead_from_incoming_email,
      )
    })
  },
})

// The account that sends the platform's own emails is not the company's to
// edit: it is left out of the list (crm.api.email_accounts, credtech#191)
getSystemEmailAccounts()
  .then((names) => {
    if (!names?.length) return
    emailAccounts.update({
      filters: { ...emailAccounts.filters, name: ['not in', names] },
    })
  })
  .finally(() => emailAccounts.reload())
</script>
