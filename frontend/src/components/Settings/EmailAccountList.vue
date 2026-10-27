<template>
  <div class="flex flex-col h-full">
    <!-- header -->
    <div class="flex justify-between text-ink-gray-8">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Email Accounts') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Connect email accounts to send and receive emails from CRM. Set one as the default for incoming and outgoing emails.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Add Account')"
          theme="gray"
          variant="solid"
          icon-left="lucide-plus"
          @click="emit('update:step', 'email-add')"
        />
      </div>
    </div>

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
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import EmptyState from '../ListViews/EmptyState.vue'
import EmailAccountCard from './EmailAccountCard.vue'
import { call, createListResource } from 'frappe-ui'

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
call('crm.api.email_accounts.get_system_email_accounts')
  .then((names) => {
    if (!names?.length) return
    emailAccounts.update({
      filters: { ...emailAccounts.filters, name: ['not in', names] },
    })
  })
  .catch((e) => console.error('[email] system accounts', e))
  .finally(() => emailAccounts.reload())
</script>
