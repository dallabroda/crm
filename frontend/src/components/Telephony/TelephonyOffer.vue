<template>
  <div class="flex flex-col items-center gap-2">
    <span class="text-center text-p-sm text-ink-gray-6">
      {{ __('Integrated telephony: API4Com, Twilio and Exotel.') }}
    </span>
    <div class="flex flex-wrap items-center justify-center gap-2">
      <Button
        v-if="isManager()"
        variant="outline"
        :label="__('Set up telephony')"
        iconLeft="lucide-settings"
        @click="openTelephonySettings"
      />
      <Button
        variant="outline"
        :label="__('Request another telephony')"
        iconLeft="lucide-phone-forwarded"
        @click="showRequest = true"
      />
    </div>
    <TelephonyRequestModal v-model="showRequest" />
  </div>
</template>

<script setup>
// The telephony companies HubTech integrates with and the way to ask for another one (credtech#259)
import TelephonyRequestModal from '@/components/Modals/TelephonyRequestModal.vue'
import { activeSettingsPage, showSettings } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { ref } from 'vue'

const { isManager } = usersStore()
const showRequest = ref(false)

function openTelephonySettings() {
  activeSettingsPage.value = __('Telephony')
  showSettings.value = true
}
</script>
