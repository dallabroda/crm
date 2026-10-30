<template>
  <template v-if="status?.enabled">
    <!-- Disabled buttons get no hover events, so the tooltip sits on a
         wrapper -->
    <Tooltip
      v-if="!status.has_cnpj"
      :text="__('Add the CNPJ to find contacts')"
    >
      <div class="inline-flex" tabindex="0">
        <Button
          :label="__('Find contacts')"
          iconLeft="lucide-users"
          disabled
        />
      </div>
    </Tooltip>
    <Button
      v-else-if="status.can_write"
      :label="running ? __('Finding contacts…') : __('Find contacts')"
      :tooltip="
        __(
          'Partners with phones (WhatsApp) and e-mails, from Assertiva Localize',
        )
      "
      iconLeft="lucide-users"
      :loading="running"
      @click="ask"
    />
  </template>
</template>

<script setup>
import { Button, Tooltip, call, toast } from 'frappe-ui'
import { onMounted, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'
import { formatDate } from '@/utils'

// Assertiva Localize (credtech#290): each partner of the organization becomes
// a contact with CPF, phones and e-mails. Queries are paid, so the saved result
// is offered first and a new paid query is always an explicit choice.
const API = 'cred_hub.integrations.localize.'

const props = defineProps({
  organization: { type: String, required: true },
  cnpj: { type: String, default: '' },
})
const emit = defineEmits(['done'])

const status = ref(null)
const running = ref(false)

async function loadStatus() {
  try {
    status.value = await call(API + 'get_status', {
      organization: props.organization,
    })
  } catch {
    // without the cred_hub app (or the permission) the button does not show
    status.value = null
  }
}

onMounted(loadStatus)
watch(() => [props.organization, props.cnpj], loadStatus)

function ask() {
  if (running.value) return
  const extra = status.value.partner_lookup
    ? ' ' + __('Plus one paid query per partner, for their phones and e-mails.')
    : ''
  if (status.value.last_query_on) {
    createDialog({
      title: __('Find contacts'),
      message:
        __(
          'This CNPJ was queried on {0}. The saved result is used at no cost; a new query is paid to Assertiva.',
          [formatDate(status.value.last_query_on)],
        ) + extra,
      size: 'md',
      actions: [
        {
          label: __('New paid query'),
          onClick: ({ close }) => {
            close()
            run(1)
          },
        },
        {
          label: __('Use saved result'),
          variant: 'solid',
          onClick: ({ close }) => {
            close()
            run(0)
          },
        },
      ],
    })
    return
  }
  createDialog({
    title: __('Find contacts'),
    message:
      __(
        'Assertiva Localize looks up the partners of this CNPJ. It is a paid query of your Assertiva contract.',
      ) + extra,
    size: 'md',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Find contacts'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          run(0)
        },
      },
    ],
  })
}

async function run(force) {
  running.value = true
  try {
    const result = await call(API + 'enrich_organization', {
      organization: props.organization,
      force,
    })
    if (!result.ok) {
      toast.error(result.message)
      return
    }
    if (!result.found) {
      toast.warning(result.message)
    } else {
      toast.success(__('Contacts found'), { description: result.message })
    }
    for (const error of result.errors || []) toast.warning(error)
    emit('done')
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not find the contacts.'))
  } finally {
    running.value = false
    loadStatus()
  }
}
</script>
