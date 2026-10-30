<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Nvoip Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="nvoip.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="nvoip.doc?.enabled && !nvoip.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="nvoip.reload()"
        />
        <Button
          v-if="nvoip.originalDoc?.enabled"
          :label="__('Disable')"
          variant="subtle"
          @click="disable"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="nvoip.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="nvoip.doc" class="h-full">
        <div v-if="nvoip.doc.enabled" class="flex flex-col gap-6">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Your company hires Nvoip directly. Calls made from a card and incoming calls land on the timeline of the deal of that number, in the name of the salesperson of the extension. Nvoip has no call webhook: calls are read every few minutes.',
              )
            }}
          </p>
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="nvoip.doc.numbersip"
              :label="__('Nvoip numbersip')"
              type="text"
              required
              autocomplete="off"
            />
            <Password
              v-model="nvoip.doc.user_token"
              :label="__('Nvoip user-token')"
              placeholder="************"
              required
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Both are in the Nvoip panel, under API. The user-token is not the same as the access_token Nvoip generates from it.',
              )
            }}
          </span>
          <ErrorMessage :message="saveError" />

          <!-- Extension of each salesperson -->
          <template v-if="nvoip.originalDoc?.enabled">
            <div class="h-px border-t border-outline-elevation-2" />
            <TelephonyExtensions
              operator="nvoip"
              :description="
                __(
                  'The Nvoip extension (numbersip of that user, or sub-account id) of each salesperson, so each call goes in their name.',
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
                {{ __('Nvoip Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Nvoip to record the calls of your Nvoip account on the timeline of your deals',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="nvoip.get.loading"
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

const { document: nvoip } = useDocument('CRM Nvoip Settings', 'CRM Nvoip Settings')

const saveError = ref('')

function enable() {
  nvoip.doc.enabled = true
}

function disable() {
  nvoip.doc.enabled = false
  update()
}

function update() {
  saveError.value = ''
  nvoip.save.submit(null, {
    onSuccess: () => {
      nvoip.reload()
      toast.success(__('Nvoip settings saved'))
    },
    // e.g. Nvoip refused the numbersip/user-token
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

// Only what this page edits: a document method would make it look unsaved
const isDirty = computed(() => {
  const doc = nvoip.doc
  const original = nvoip.originalDoc
  if (!doc || !original) return false
  return (
    Boolean(doc.enabled) !== Boolean(original.enabled) ||
    (doc.numbersip || '') !== (original.numbersip || '') ||
    (doc.user_token || '') !== (original.user_token || '')
  )
})
</script>
