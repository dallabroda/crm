<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Zenvia Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="zenvia.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <div v-if="zenvia.doc?.enabled && !zenvia.get.loading" class="flex gap-2">
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="zenvia.reload()"
        />
        <Button
          v-if="zenvia.originalDoc?.enabled"
          :label="__('Disable')"
          variant="subtle"
          @click="disable"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="zenvia.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="zenvia.doc" class="h-full">
        <div v-if="zenvia.doc.enabled" class="flex flex-col gap-6">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Your company hires Zenvia directly. A call made from a card rings the salesperson first, then the customer, and lands on the timeline of that deal with its recording. Calls made from a Zenvia extension and calls received on your numbers land on the deals of that number.',
              )
            }}
          </p>
          <div class="grid grid-cols-2 gap-4">
            <Password
              v-model="zenvia.doc.access_token"
              :label="__('Zenvia access token')"
              placeholder="************"
              required
            />
            <FormControl
              v-model="zenvia.doc.caller_number"
              :label="__('Number shown to the customer (optional)')"
              type="text"
              placeholder="+5548999990000"
              autocomplete="off"
            />
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The access token is in the Zenvia voice panel, under Minha Conta.',
              )
            }}
          </span>
          <ErrorMessage :message="saveError" />

          <template v-if="zenvia.originalDoc?.enabled">
            <!-- Webhooks: Zenvia has no API to register them, so they are pasted in its panel -->
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="flex flex-col gap-2">
              <div class="text-base-medium text-ink-gray-8">
                {{ __('Call webhooks') }}
              </div>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Paste each address in the Zenvia voice panel, under Desenvolvedores > Configurações da API. Zenvia may take up to 20 minutes to start sending.',
                  )
                }}
              </span>
              <div
                v-for="hook in webhooks"
                :key="hook.key"
                class="flex flex-col gap-1"
              >
                <span class="text-p-sm text-ink-gray-7">{{ hook.label }}</span>
                <div class="flex items-center gap-2">
                  <TextInput
                    class="flex-1"
                    :model-value="hook.url"
                    readonly
                    @focus="$event.target.select()"
                  />
                  <Button
                    :label="__('Copy')"
                    icon-left="lucide-copy"
                    :disabled="!hook.url"
                    @click="copyUrl(hook.url)"
                  />
                </div>
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
                        'The current addresses stop working at once; paste the new ones in the Zenvia panel.',
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
                    :loading="zenvia.regenerateSecret.loading"
                    @click="regenerate"
                  />
                </template>
              </div>
            </div>

            <!-- Extension of each salesperson -->
            <div class="h-px border-t border-outline-elevation-2" />
            <TelephonyExtensions
              operator="zenvia"
              :description="
                __(
                  'The Zenvia extension (2 to 6 digits) or the phone in international format (+5548999990000) of each salesperson: Zenvia rings it first, then the customer.',
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
                {{ __('Zenvia Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable Zenvia to call your customers from a card and record the calls on the timeline of your deals',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="zenvia.get.loading"
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
import { TextInput, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const emit = defineEmits(['updateStep'])

const { document: zenvia } = useDocument(
  'CRM Zenvia Settings',
  'CRM Zenvia Settings',
  {
    whitelistedMethods: {
      webhookUrls: { method: 'get_webhook_urls' },
      regenerateSecret: { method: 'regenerate_webhook_secret' },
    },
  },
)

const saveError = ref('')
const confirmRegenerate = ref(false)

const webhooks = computed(() => {
  const urls = zenvia.webhookUrls?.data || {}
  return [
    { key: 'chamada_fim', label: __('Chamada - Fim'), url: urls.chamada_fim || '' },
    { key: 'did_fim', label: __('DID - Fim de Chamada'), url: urls.did_fim || '' },
  ]
})

watch(
  () => zenvia.originalDoc?.enabled,
  (enabled) => {
    if (enabled) zenvia.webhookUrls.submit()
  },
  { immediate: true },
)

function enable() {
  zenvia.doc.enabled = true
}

function disable() {
  zenvia.doc.enabled = false
  update()
}

function regenerate() {
  zenvia.regenerateSecret.submit(null, {
    onSuccess: () => {
      confirmRegenerate.value = false
      zenvia.reload()
      zenvia.webhookUrls.submit()
      toast.success(__('New secret generated: paste the new addresses in the Zenvia panel'))
    },
    onError: (err) => toast.error(err.messages?.[0] || err.message),
  })
}

async function copyUrl(url) {
  await navigator.clipboard.writeText(url)
  toast.success(__('Copied'))
}

function update() {
  saveError.value = ''
  zenvia.save.submit(null, {
    onSuccess: () => {
      zenvia.reload()
      zenvia.webhookUrls.submit()
      toast.success(__('Zenvia settings saved'))
    },
    // e.g. Zenvia refused the credentials
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

// Only what this page edits: the document methods (webhook addresses, new
// secret) answer with the document and would make it look unsaved
const isDirty = computed(() => {
  const doc = zenvia.doc
  const original = zenvia.originalDoc
  if (!doc || !original) return false
  return (
    Boolean(doc.enabled) !== Boolean(original.enabled) ||
    (doc.access_token || '') !== (original.access_token || '') ||
    (doc.caller_number || '') !== (original.caller_number || '')
  )
})
</script>
