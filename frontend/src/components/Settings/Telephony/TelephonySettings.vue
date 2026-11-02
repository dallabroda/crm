<template>
  <div class="flex h-full flex-col gap-6">
    <SettingsPageHeader :title="__('Telephony Settings')">
      <template #badge>
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </template>
      <template #description>
        {{ __('Configure telephony settings for your CRM.') }}
      </template>
      <template #actions>
        <template v-if="isDirty">
          <Button
            v-if="isDirty"
            :loading="
              isNewDoc ? insertResource.loading : telephonyAgent.save?.loading
            "
            :label="__('Update')"
            variant="solid"
            @click="update"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <div v-if="telephonyAgent.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-6 py-3">
        <div class="flex flex-col">
          <div class="truncate text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Default Medium') }}
          </div>
          <div class="text-base leading-5 text-ink-gray-6">
            {{ __('Default calling medium for logged-in user') }}
          </div>
        </div>
        <div class="flex items-center gap-1">
          <FormControl
            v-model="telephonyAgent.doc.default_medium"
            variant="outline"
            type="select"
            class="w-44"
            :options="[
              { label: __(''), value: '' },
              { label: __('Twilio'), value: 'Twilio' },
              { label: __('Exotel'), value: 'Exotel' },
              ...Object.values(voipOperators).map((medium) => ({
                label: medium,
                value: medium,
              })),
            ]"
            :placeholder="__('Select Medium')"
          />
          <Button
            v-if="telephonyAgent.doc.default_medium"
            icon="lucide-x"
            :tooltip="__('Clear')"
            @click="telephonyAgent.doc.default_medium = ''"
          />
        </div>
      </div>
      <div
        v-if="isEnabled('twilio')"
        class="h-px border-t border-outline-gray-2"
      />
      <div
        v-if="isEnabled('twilio')"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col">
          <div class="truncate text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Twilio Number') }}
          </div>
          <div class="text-base leading-5 text-ink-gray-6">
            {{ __('Set the Twilio number to be used for outgoing calls.') }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.twilio_number"
            variant="outline"
            class="flex-1 truncate w-44"
            :placeholder="__('Enter Twilio Number')"
            :error="
              Boolean(telephonyAgent.doc.twilio_number) &&
              !validatePhone(telephonyAgent.doc.twilio_number)
                ? __('Enter a valid phone number')
                : undefined
            "
            placement="bottom-end"
          />
        </div>
      </div>
      <div
        v-if="isEnabled('exotel')"
        class="h-px border-t border-outline-gray-2"
      />
      <div
        v-if="isEnabled('exotel')"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col">
          <div class="truncate text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Exotel Number') }}
          </div>
          <div class="text-base leading-5 text-ink-gray-6">
            {{ __('Set the Exotel number to be used for outgoing calls.') }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.exotel_number"
            variant="outline"
            class="flex-1 truncate w-44"
            :placeholder="__('Enter Exotel Number')"
            :error="
              Boolean(telephonyAgent.doc.exotel_number) &&
              !validatePhone(telephonyAgent.doc.exotel_number)
                ? __('Enter a valid phone number')
                : undefined
            "
            placement="bottom-end"
          />
        </div>
      </div>
      <div
        v-if="isEnabled('exotel')"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col">
          <div class="truncate text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Personal Mobile Number') }}
          </div>
          <div class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Enter your personal mobile number used by Exotel to make calls',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="telephonyAgent.doc.mobile_no"
            variant="outline"
            class="flex-1 truncate w-44"
            :placeholder="__('Enter Personal Mobile Number')"
            :error="
              Boolean(telephonyAgent.doc.mobile_no) &&
              !validatePhone(telephonyAgent.doc.mobile_no)
                ? __('Enter a valid phone number')
                : undefined
            "
            placement="bottom-end"
          />
        </div>
      </div>

      <div
        v-if="isManager()"
        class="mt-4 flex items-center justify-between py-3 text-lg font-medium leading-6 text-ink-gray-9"
      >
        {{ __('Integrations') }}
      </div>

      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Twilio') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __('Configure your Twilio telephony integration settings here')
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="
            isEnabled('twilio') ? __('Update Configuration') : __('Configure')
          "
          @click="emit('updateStep', 'twilio-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Exotel') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __('Configure your Exotel telephony integration settings here')
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="
            isEnabled('exotel') ? __('Update Configuration') : __('Configure')
          "
          @click="emit('updateStep', 'exotel-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <!-- Call logging only: calls made at API4Com land on the deal timeline (credtech#98) -->
      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('API4Com') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Record the calls of your API4Com account on the timeline of your deals',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Configure')"
          @click="emit('updateStep', 'api4com-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <!-- No webhook: calls are read every few minutes (credtech#269) -->
      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Nvoip') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Record the calls of your Nvoip account on the timeline of your deals',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Configure')"
          @click="emit('updateStep', 'nvoip-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <!-- Call logging only, same as API4Com; no click-to-call yet (credtech#271) -->
      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Wavix') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Record the calls of your Wavix account on the timeline of your deals',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Configure')"
          @click="emit('updateStep', 'wavix-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <!-- Click-to-call through a Call Control Application (credtech#270) -->
      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Telnyx') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Call your customers from a card through Telnyx and record the calls on your deals',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Configure')"
          @click="emit('updateStep', 'telnyx-settings')"
        />
      </div>

      <div v-if="isManager()" class="h-px border-t border-outline-gray-2" />

      <!-- Zenvia Voz, former TotalVoice (credtech#272) -->
      <div
        v-if="isManager()"
        class="flex items-center justify-between gap-6 py-3"
      >
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Zenvia') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Call your customers from a card through Zenvia and record the calls on your deals',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Configure')"
          @click="emit('updateStep', 'zenvia-settings')"
        />
      </div>
      <div class="h-px border-t border-outline-gray-2" />
      <div class="flex items-center justify-between gap-6 py-3">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium leading-5 text-ink-gray-9">
            {{ __('Another telephony company') }}
          </span>
          <span class="text-base leading-5 text-ink-gray-6">
            {{
              __(
                'Use another telephony? Ask for the integration: CredTech studies it from the API documentation.',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          :label="__('Request integration')"
          @click="showTelephonyRequest = true"
        />
      </div>
      <TelephonyRequestModal v-model="showTelephonyRequest" />
    </div>
    <ErrorMessage
      :message="isNewDoc ? insertResource.error : telephonyAgent.save?.error"
    />
  </div>
</template>
<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import {
  FormControl,
  Badge,
  ErrorMessage,
  createResource,
  toast,
} from 'frappe-ui'
import TelephonyRequestModal from '@/components/Modals/TelephonyRequestModal.vue'
import { useTelephony, voipOperators } from '@/composables/telephony'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { validatePhone } from '@/utils'
import { ref, computed } from 'vue'

const { isEnabled } = useTelephony()

const emit = defineEmits(['updateStep'])

// credtech#259: ask CredTech for another telephony integration
const showTelephonyRequest = ref(false)

const { getUser, isManager } = usersStore()

const isNewDoc = ref(false)

const { document: telephonyAgent } = useDocument(
  'CRM Telephony Agent',
  getUser().name,
  {
    onError: (err) => {
      if (err.exc_type === 'DoesNotExistError') {
        isNewDoc.value = true
        telephonyAgent.doc = {}
        telephonyAgent.originalDoc = {}
      }
    },
  },
)

const insertResource = createResource({
  url: 'frappe.client.insert',
  onSuccess: (data) => {
    isNewDoc.value = false
    telephonyAgent.doc = data
    telephonyAgent.originalDoc = JSON.parse(JSON.stringify(data))
    toast.success(__('Document created successfully'))
  },
  onError: (err) => {
    err.messages?.forEach((msg) => toast.error(msg))
  },
})

function update() {
  if (!isDirty.value) return

  if (isNewDoc.value) {
    insertResource.submit({
      doc: {
        doctype: 'CRM Telephony Agent',
        user: getUser().name,
        ...telephonyAgent.doc,
      },
    })
  } else {
    telephonyAgent.save.submit()
  }
}

const isDirty = computed(() => {
  return (
    telephonyAgent.doc &&
    telephonyAgent.originalDoc &&
    JSON.stringify(telephonyAgent.doc) !==
      JSON.stringify(telephonyAgent.originalDoc)
  )
})
</script>
