<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Wavix Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="wavix.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <div
        v-if="wavix.doc?.enabled && !wavix.get.loading"
        class="flex gap-2"
      >
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="wavix.reload()"
        />
        <Button
          v-if="wavix.originalDoc?.enabled"
          :label="__('Disable')"
          variant="subtle"
          @click="disable"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="wavix.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="wavix.doc" class="h-full">
        <div v-if="wavix.doc.enabled" class="flex flex-col gap-6">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Your company hires Wavix directly. Each call lands on the timeline of the deal of that number. Calling from a card is not ready yet: it needs the Wavix Embeddable browser widget, still pending confirmation with a real account.',
              )
            }}
          </p>
          <div class="flex flex-col gap-1.5">
            <Password
              v-model="wavix.doc.api_key"
              :label="__('Wavix API key')"
              placeholder="************"
              required
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Create a key in the Wavix panel and paste it here. It is never shown again.',
                )
              }}
            </span>
          </div>
          <ErrorMessage :message="saveError" />

          <!-- Webhook: registered at Wavix by the CRM itself -->
          <template v-if="wavix.originalDoc?.enabled">
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="flex flex-col gap-2">
              <div class="text-base-medium text-ink-gray-8">
                {{ __('Call webhook') }}
              </div>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Registered at Wavix automatically when the key is saved. Only needed by hand if Wavix support asks for it.',
                  )
                }}
              </span>
              <div class="flex items-center gap-2">
                <TextInput
                  class="flex-1"
                  :model-value="webhookUrl"
                  readonly
                  @focus="$event.target.select()"
                />
                <Button
                  :label="__('Copy')"
                  icon-left="lucide-copy"
                  :disabled="!webhookUrl"
                  @click="copyUrl"
                />
              </div>
              <div class="flex items-center gap-2">
                <Button
                  v-if="!confirmRegenerate"
                  :label="__('Generate new secret')"
                  icon-left="lucide-refresh-cw"
                  @click="confirmRegenerate = true"
                />
                <template v-else>
                  <span class="text-p-sm text-ink-red-4">
                    {{
                      __(
                        'The current address stops working at once and the new one is registered at Wavix.',
                      )
                    }}
                  </span>
                  <Button
                    :label="__('Cancel')"
                    variant="subtle"
                    @click="confirmRegenerate = false"
                  />
                  <Button
                    :label="__('Generate')"
                    theme="red"
                    variant="solid"
                    :loading="wavix.regenerateSecret.loading"
                    @click="regenerate"
                  />
                </template>
              </div>
            </div>
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
                {{ __('Wavix Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Wavix to record the calls of your Wavix account on the timeline of your deals',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="wavix.get.loading"
        class="flex items-center justify-center mt-[35%]"
      >
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { useDocument } from '@/data/document'
import { TextInput, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: wavix } = useDocument(
  'CRM Wavix Settings',
  'CRM Wavix Settings',
  {
    whitelistedMethods: {
      webhookUrl: { method: 'get_webhook_url' },
      regenerateSecret: { method: 'regenerate_webhook_secret' },
    },
  },
)

const saveError = ref('')
const confirmRegenerate = ref(false)

const webhookUrl = computed(() => wavix.webhookUrl?.data || '')

watch(
  () => wavix.originalDoc?.enabled,
  (enabled) => {
    if (enabled) wavix.webhookUrl.submit()
  },
  { immediate: true },
)

function enable() {
  wavix.doc.enabled = true
}

function disable() {
  wavix.doc.enabled = false
  update()
}

function update() {
  saveError.value = ''
  wavix.save.submit(null, {
    onSuccess: () => {
      wavix.reload()
      toast.success(__('Wavix settings saved'))
    },
    // e.g. Wavix refused the key: the settings are not saved
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

function regenerate() {
  wavix.regenerateSecret.submit(null, {
    onSuccess: () => {
      confirmRegenerate.value = false
      wavix.reload()
      wavix.webhookUrl.submit()
      toast.success(__('New secret generated and registered at Wavix'))
    },
    onError: (err) => toast.error(err.messages?.[0] || err.message),
  })
}

async function copyUrl() {
  await navigator.clipboard.writeText(webhookUrl.value)
  toast.success(__('Copied'))
}

// Only what this page edits: the document methods (webhook address, new
// secret) answer with the document and would make it look unsaved
const isDirty = computed(() => {
  const doc = wavix.doc
  const original = wavix.originalDoc
  if (!doc || !original) return false
  return (
    Boolean(doc.enabled) !== Boolean(original.enabled) ||
    (doc.api_key || '') !== (original.api_key || '')
  )
})
</script>
