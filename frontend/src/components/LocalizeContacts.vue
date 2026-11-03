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
          variant="outline"
          :label="__('Find contacts')"
          iconLeft="lucide-users"
          disabled
        />
      </div>
    </Tooltip>
    <Button
      v-else-if="status.can_write"
      variant="outline"
      :class="{ 'ct-btn-accent-text': accent }"
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
  <!-- Figma "Organizações · Detalhe · Buscar contatos" (1331:21044): 448px
       modal, 20 Semi Bold title with a ghost close button, one paragraph per
       message and the actions on a gray footer. -->
  <Dialog v-model:open="dialog.show" size="md" bare>
    <div class="flex items-center gap-3 pb-2 pl-6 pr-4 pt-5">
      <Dialog.Title
        as="h3"
        class="flex-1 truncate text-[20px] font-semibold leading-7 text-ink-gray-9"
      >
        {{ __('Find contacts') }}
      </Dialog.Title>
      <Button
        variant="ghost"
        size="lg"
        icon="lucide-x"
        :aria-label="__('Close')"
        @click="dialog.show = false"
      />
    </div>
    <Dialog.Description
      as="div"
      class="flex flex-col gap-4 px-6 pb-6 text-p-base text-ink-gray-6"
    >
      <p v-for="text in dialog.paragraphs" :key="text">{{ text }}</p>
    </Dialog.Description>
    <div
      class="flex flex-wrap items-center justify-end gap-3 bg-[var(--ct-bg-soft)] px-6 py-4"
    >
      <Button
        v-for="action in dialog.actions"
        :key="action.label"
        :variant="action.variant || 'outline'"
        :class="
          action.variant
            ? ''
            : 'border-[var(--ct-border-strong)] hover:border-[var(--ct-border-strong)]'
        "
        :label="action.label"
        @click="action.onClick"
      />
    </div>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, Tooltip, call, toast } from 'frappe-ui'
import { onMounted, reactive, ref, watch } from 'vue'
import { formatDate } from '@/utils'

// Assertiva Localize (credtech#290): each partner of the organization becomes
// a contact with CPF, phones and e-mails. Queries are paid, so the saved result
// is offered first and a new paid query is always an explicit choice.
const API = 'cred_hub.integrations.localize.'

const props = defineProps({
  organization: { type: String, required: true },
  cnpj: { type: String, default: '' },
  // blue label and icon (Figma "Enviar a protesto" modal, comment 1992559997)
  accent: { type: Boolean, default: false },
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

const dialog = reactive({ show: false, paragraphs: [], actions: [] })

function openDialog(paragraphs, actions) {
  Object.assign(dialog, { show: true, paragraphs, actions })
}

function choose(force) {
  dialog.show = false
  run(force)
}

function ask() {
  if (running.value) return
  const extra = status.value.partner_lookup
    ? [__('Plus one paid query per partner, for their phones and e-mails.')]
    : []
  if (status.value.last_query_on) {
    openDialog(
      [
        __(
          'This CNPJ was queried on {0}. The saved result is used at no cost; a new query is paid to Assertiva.',
          [formatDate(status.value.last_query_on, '', true)],
        ),
        ...extra,
      ],
      [
        { label: __('New paid query'), onClick: () => choose(1) },
        {
          label: __('Use saved result'),
          variant: 'solid',
          onClick: () => choose(0),
        },
      ],
    )
    return
  }
  openDialog(
    [
      __(
        'Assertiva Localize looks up the partners of this CNPJ. It is a paid query of your Assertiva contract.',
      ),
      ...extra,
    ],
    [
      { label: __('Cancel'), onClick: () => (dialog.show = false) },
      {
        label: __('Find contacts'),
        variant: 'solid',
        onClick: () => choose(0),
      },
    ],
  )
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
