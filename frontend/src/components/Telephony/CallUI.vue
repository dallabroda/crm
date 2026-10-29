<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <Dialog
    v-model:open="show"
    :title="__('Make Call')"
    :actions="[
      {
        label: __('Call using {0}', [callMedium]),
        variant: 'solid',
        onClick: makeCallUsing,
      },
    ]"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="mobileNumber"
          type="text"
          :label="__('Mobile Number')"
        />
        <FormControl
          v-model="callMedium"
          type="select"
          :label="__('Calling Medium')"
          :options="enabledIntegrations.map(({ label }) => label)"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            v-model="isDefaultMedium"
            type="checkbox"
            :label="__('Make {0} as default calling medium', [callMedium])"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __('You can change the default calling medium from the settings')
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import TwilioCallUI from '@/components/Telephony/TwilioCallUI.vue'
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import {
  defaultCallingMedium,
  useTelephony,
  voipOperators,
} from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import { FormControl, call, toast } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const { setMakeCall } = globalStore()
const { isEnabled, isAnyEnabled } = useTelephony()

const twilio = ref(null)
const exotel = ref(null)

const callMedium = ref('Twilio')
const isDefaultMedium = ref(false)

const show = ref(false)
const mobileNumber = ref('')
const deal = ref(null)

// Twilio and Exotel call from the browser (their own UI); the other operators
// are called through the server, which asks the operator to ring the user's
// extension (credtech#268)
const enabledIntegrations = computed(() =>
  [
    { key: 'twilio', label: 'Twilio', ref: twilio },
    { key: 'exotel', label: 'Exotel', ref: exotel },
    ...Object.entries(voipOperators.value).map(([key, label]) => ({
      key,
      label,
      ref: null,
    })),
  ].filter(({ key }) => isEnabled(key)),
)

function makeCall(number, dealName = null) {
  deal.value = dealName
  const labels = enabledIntegrations.value.map(({ label }) => label)
  const defaultMedium = labels.includes(defaultCallingMedium.value)
    ? defaultCallingMedium.value
    : null

  if (enabledIntegrations.value.length > 1 && !defaultMedium) {
    mobileNumber.value = number
    show.value = true
    return
  }

  callMedium.value = defaultMedium || labels[0] || 'Twilio'
  mobileNumber.value = number
  makeCallUsing()
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium()
  }

  if (callMedium.value === 'Twilio') {
    twilio.value.makeOutgoingCall(mobileNumber.value)
  }

  if (callMedium.value === 'Exotel') {
    exotel.value.makeOutgoingCall(mobileNumber.value)
  }

  if (Object.values(voipOperators.value).includes(callMedium.value)) {
    callThroughServer(callMedium.value, mobileNumber.value, deal.value)
  }
  show.value = false
}

async function callThroughServer(medium, number, dealName) {
  try {
    await call('crm.integrations.voip.api.make_call', {
      number,
      medium,
      deal: dealName,
    })
    toast.success(
      __('Calling {0}: answer on your {1} extension first', [number, medium]),
    )
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not make the call'))
  }
}

async function setDefaultCallingMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: callMedium.value,
  })

  defaultCallingMedium.value = callMedium.value
  toast.success(
    __('Default calling medium set successfully to {0}', [callMedium.value]),
  )
}

watch(
  isAnyEnabled,
  () =>
    nextTick(() => {
      for (const { label, ref: integrationRef } of enabledIntegrations.value) {
        // server-side operators have no browser client to set up
        integrationRef?.value?.setup()
        callMedium.value = label
      }

      if (isAnyEnabled.value) {
        callMedium.value = enabledIntegrations.value[0]?.label ?? 'Twilio'
        setMakeCall(makeCall)
      }
    }),
  { immediate: true },
)
</script>
