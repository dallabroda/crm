<template>
  <TelephonySettings
    v-if="step === 'telephony-settings'"
    @updateStep="updateStep"
  />
  <TwilioSettings
    v-else-if="step === 'twilio-settings'"
    @updateStep="updateStep"
  />
  <ExotelSettings
    v-else-if="step === 'exotel-settings'"
    @updateStep="updateStep"
  />
  <API4ComSettings
    v-else-if="step === 'api4com-settings'"
    @updateStep="updateStep"
  />
  <NvoipSettings
    v-else-if="step === 'nvoip-settings'"
    @updateStep="updateStep"
  />
  <WavixSettings
    v-else-if="step === 'wavix-settings'"
    @updateStep="updateStep"
  />
  <TelnyxSettings
    v-else-if="step === 'telnyx-settings'"
    @updateStep="updateStep"
  />
</template>
<script setup>
import TelephonySettings from './TelephonySettings.vue'
import ExotelSettings from './ExotelSettings.vue'
import TwilioSettings from './TwilioSettings.vue'
import API4ComSettings from './API4ComSettings.vue'
import NvoipSettings from './NvoipSettings.vue'
import WavixSettings from './WavixSettings.vue'
import TelnyxSettings from './TelnyxSettings.vue'
import { ref } from 'vue'

const step = ref('telephony-settings')

function updateStep(newStep) {
  step.value = newStep
}
</script>
