<template>
  <div class="flex flex-col h-full">
    <SettingsPageHeader :title="__('Email Accounts')">
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

    <!-- list accounts -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="mt-4"
    >
      <div
        v-for="(emailAccount, i) in emailAccounts.data"
        :key="emailAccount.name"
      >
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
        <div
          v-if="emailAccounts.data.length !== i + 1"
          class="h-px border-t mx-2 border-outline-elevation-2"
        />
      </div>
    </div>
    <!-- fallback if no email accounts -->
    <EmptyState
      v-else
      name="Email Accounts"
      :description="__('Add one to get started.')"
      :icon="Email2Icon"
    />
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmptyState from '../ListViews/EmptyState.vue'
import EmailAccountCard from './EmailAccountCard.vue'
import { getSystemEmailAccounts } from './emailConfig'
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
