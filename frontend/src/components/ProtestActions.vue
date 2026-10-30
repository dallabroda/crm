<template>
  <Dropdown v-if="visible" :options="options" align="end">
    <template #default="{ open }">
      <Button
        :label="label"
        :loading="running"
        :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        iconLeft="lucide-landmark"
      />
    </template>
  </Dropdown>
  <Dialog
    v-model:open="showWithdraw"
    :title="__('Withdraw or cancel the protest')"
    size="md"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'CENPROT receives the request at once: removal before the registry, withdrawal before the protest, or cancellation of the protest. The registry may charge fees.',
            )
          }}
        </p>
        <FormControl
          v-model="justification"
          type="textarea"
          :label="__('Reason')"
          :placeholder="__('Commercial agreement')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="showWithdraw = false" />
        <Button
          :label="__('Ask the registry')"
          variant="solid"
          theme="red"
          @click="withdraw"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, Dropdown, FormControl, call, toast } from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'

// Protest at the registry through CENPROT (credtech#290): send, follow and
// withdraw the title of a card of the collection pipeline. The cred_hub app
// answers; without it (or with CENPROT off) nothing shows.
const API = 'cred_hub.integrations.protest.'

const props = defineProps({
  deal: { type: String, required: true },
  pipeline: { type: String, default: '' },
})
const emit = defineEmits(['done'])

const status = ref(null)
const running = ref(false)
const showWithdraw = ref(false)
const justification = ref('')

async function loadStatus() {
  try {
    status.value = await call(API + 'get_status', { deal: props.deal })
  } catch {
    status.value = null
  }
}

onMounted(loadStatus)
watch(() => [props.deal, props.pipeline], loadStatus)

const visible = computed(
  () =>
    status.value?.enabled && (status.value.in_pipeline || status.value.sent_at),
)
const label = computed(() =>
  status.value?.status
    ? __('Protest: {0}', [status.value.status])
    : __('Protest'),
)

const options = computed(() => {
  const s = status.value || {}
  return [
    s.can_write &&
      s.can_send && {
        label: s.sent_at ? __('Send to protest again') : __('Send to protest'),
        icon: 'lucide-send',
        onClick: confirmSend,
      },
    s.sent_at && {
      label: __('Update registry status'),
      icon: 'lucide-refresh-cw',
      onClick: () => run('refresh'),
    },
    s.can_write &&
      s.can_withdraw && {
        label: __('Withdraw or cancel the protest'),
        icon: 'lucide-undo-2',
        onClick: () => {
          justification.value = ''
          showWithdraw.value = true
        },
      },
  ].filter(Boolean)
})

function confirmSend() {
  createDialog({
    title: __('Send to protest'),
    message: __(
      'The title of this card goes to CENPROT now, in the name of the creditor of the settings, against the organization of the card. Registry fees may apply.',
    ),
    size: 'md',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Send to protest'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          run('send')
        },
      },
    ],
  })
}

function withdraw() {
  showWithdraw.value = false
  run('withdraw', { justification: justification.value })
}

async function run(method, args = {}) {
  running.value = true
  try {
    const result = await call(API + method, { deal: props.deal, ...args })
    if (result.ok) {
      toast.success(result.message || __('Done'))
    } else {
      toast.error(result.message)
    }
    emit('done')
  } catch (error) {
    // the title is missing data (debtor address, due date...): nothing was sent
    toast.error(error.messages?.[0] || __('Could not reach CENPROT.'))
  } finally {
    running.value = false
    loadStatus()
  }
}
</script>
