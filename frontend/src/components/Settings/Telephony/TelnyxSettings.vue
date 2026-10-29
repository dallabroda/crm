<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Telnyx Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="telnyx.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="telnyx.doc?.enabled && !telnyx.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="telnyx.reload()"
        />
        <Button
          v-if="telnyx.originalDoc?.enabled"
          :label="__('Disable')"
          variant="subtle"
          @click="disable"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="telnyx.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="telnyx.doc" class="h-full">
        <div v-if="telnyx.doc.enabled" class="flex flex-col gap-6">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Your company hires Telnyx directly. A call made from a card rings the salesperson first, then the customer, and lands on the timeline of that deal with its recording. Calls go through your Call Control Application; your numbers keep their own routing for incoming calls.',
              )
            }}
          </p>
          <div class="grid grid-cols-2 gap-4">
            <Password
              v-model="telnyx.doc.api_key"
              :label="__('Telnyx API key')"
              placeholder="************"
              required
            />
            <FormControl
              v-model="telnyx.doc.connection_id"
              :label="__('Call Control Application ID')"
              type="text"
              required
              autocomplete="off"
            />
            <FormControl
              v-model="telnyx.doc.caller_number"
              :label="__('Number shown to the customer')"
              type="text"
              placeholder="+5548999990000"
              required
              autocomplete="off"
            />
            <FormControl
              v-model="telnyx.doc.public_key"
              :label="__('Webhook public key')"
              type="text"
              required
              autocomplete="off"
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'In the Telnyx portal: API key and public key under Account Settings > Keys & Credentials; the application ID under Voice > Programmable Voice. The application needs an outbound voice profile that allows calls to your customers.',
              )
            }}
          </span>
          <ErrorMessage :message="saveError" />

          <!-- Extension of each salesperson -->
          <template v-if="telnyx.originalDoc?.enabled">
            <div class="h-px border-t border-outline-elevation-2" />
            <TelephonyExtensions
              operator="telnyx"
              :description="
                __(
                  'The phone of each salesperson in international format (+5548999990000) or their SIP address (sip:name@domain): Telnyx rings it first, then the customer.',
                )
              "
            />
          </template>
        </div>
        <!--  Disabled state -->
        <div v-else class="relative flex h-full w-full justify-center">
          <div
            class="absolute left-1/2 flex w-72 -translate-x-1/2 flex-col items-center gap-3"
            :style="{ top: '35%' }"
          >
            <div class="flex flex-col items-center gap-1.5 text-center">
              <PhoneIcon class="size-7.5 text-ink-gray-7" />
              <span class="text-lg-medium text-ink-gray-8">
                {{ __('Telnyx Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Telnyx to call your customers from a card and record the calls on the timeline of your deals',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="telnyx.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TelephonyExtensions from '@/components/Settings/Telephony/TelephonyExtensions.vue'
import { useDocument } from '@/data/document'
import { toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: telnyx } = useDocument('CRM Telnyx Settings', 'CRM Telnyx Settings')

const saveError = ref('')

function enable() {
  telnyx.doc.enabled = true
}

function disable() {
  telnyx.doc.enabled = false
  update()
}

function update() {
  saveError.value = ''
  telnyx.save.submit(null, {
    onSuccess: () => {
      telnyx.reload()
      toast.success(__('Telnyx settings saved'))
    },
    // e.g. Telnyx refused the credentials
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

// Only what this page edits: a document method would make it look unsaved
const isDirty = computed(() => {
  const doc = telnyx.doc
  const original = telnyx.originalDoc
  if (!doc || !original) return false
  return (
    Boolean(doc.enabled) !== Boolean(original.enabled) ||
    (doc.api_key || '') !== (original.api_key || '') ||
    (doc.connection_id || '') !== (original.connection_id || '') ||
    (doc.caller_number || '') !== (original.caller_number || '') ||
    (doc.public_key || '') !== (original.public_key || '')
  )
})
</script>
