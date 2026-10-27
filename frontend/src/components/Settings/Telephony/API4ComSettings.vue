<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('API4Com Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'telephony-settings')"
        />
        <Badge
          v-if="api4com.doc?.enabled && isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <div
        v-if="api4com.doc?.enabled && !api4com.get.loading"
        class="flex gap-2"
      >
        <Button
          v-if="isDirty"
          :label="__('Discard Changes')"
          variant="subtle"
          @click="api4com.reload()"
        />
        <Button
          v-if="api4com.originalDoc?.enabled"
          :label="__('Disable')"
          variant="subtle"
          @click="disable"
        />
        <Button
          variant="solid"
          :label="__('Update')"
          :loading="api4com.save.loading"
          :disabled="!isDirty"
          @click="update"
        />
      </div>
    </template>
    <template #content>
      <div v-if="api4com.doc" class="h-full">
        <div v-if="api4com.doc.enabled" class="flex flex-col gap-6">
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Your company hires API4Com directly. Each call made or received at API4Com lands on the timeline of the deal of that number, in the name of the salesperson of the extension.',
              )
            }}
          </p>
          <div class="flex flex-col gap-1.5">
            <Password
              v-model="api4com.doc.api_token"
              :label="__('API4Com API token')"
              placeholder="************"
              required
            />
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Create a token that does not expire in the API4Com panel and paste it here. It is never shown again.',
                )
              }}
            </span>
          </div>
          <ErrorMessage :message="saveError" />

          <!-- Webhook: registered at API4Com by the CRM itself -->
          <template v-if="api4com.originalDoc?.enabled">
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="flex flex-col gap-2">
              <div class="text-base-medium text-ink-gray-8">
                {{ __('Call webhook') }}
              </div>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'Registered at API4Com automatically when the token is saved. Only needed by hand if API4Com support asks for it.',
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
                        'The current address stops working at once and the new one is registered at API4Com.',
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
                    :loading="api4com.regenerateSecret.loading"
                    @click="regenerate"
                  />
                </template>
              </div>
            </div>

            <!-- Extension of each salesperson -->
            <div class="h-px border-t border-outline-elevation-2" />
            <div class="flex flex-col gap-2">
              <div class="text-base-medium text-ink-gray-8">
                {{ __('Extensions') }}
              </div>
              <span class="text-p-sm text-ink-gray-6">
                {{
                  __(
                    'The API4Com extension of each user, so each call goes in the name of who made or answered it.',
                  )
                }}
              </span>
              <ul class="flex flex-col divide-y divide-outline-elevation-2">
                <li
                  v-for="user in crmUsers"
                  :key="user.name"
                  class="flex items-center justify-between gap-4 py-2"
                >
                  <div class="flex flex-col">
                    <span class="text-p-base text-ink-gray-8">
                      {{ user.full_name }}
                    </span>
                    <span class="text-p-sm text-ink-gray-5">
                      {{ user.name }}
                    </span>
                  </div>
                  <TextInput
                    class="w-32"
                    :model-value="extensions[user.name] || ''"
                    :placeholder="__('Extension')"
                    @change="saveExtension(user.name, $event.target.value)"
                  />
                </li>
              </ul>
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
                {{ __('API4Com Integration Disabled') }}
              </span>
              <span class="text-center text-p-base text-ink-gray-6">
                {{
                  __(
                    'Enable API4Com to record the calls of your API4Com account on the timeline of your deals',
                  )
                }}
              </span>
              <Button :label="__('Enable')" variant="solid" @click="enable" />
            </div>
          </div>
        </div>
      </div>
      <div
        v-else-if="api4com.get.loading"
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
import { usersStore } from '@/stores/users'
import { call, createListResource, TextInput, toast } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const emit = defineEmits(['updateStep'])

const API = 'crm.fcrm.doctype.crm_api4com_settings.crm_api4com_settings.'

const { users } = usersStore()

const { document: api4com } = useDocument(
  'CRM API4Com Settings',
  'CRM API4Com Settings',
  {
    whitelistedMethods: {
      webhookUrl: { method: 'get_webhook_url' },
      regenerateSecret: { method: 'regenerate_webhook_secret' },
    },
  },
)

const saveError = ref('')
const confirmRegenerate = ref(false)

const webhookUrl = computed(() => api4com.webhookUrl?.data || '')

watch(
  () => api4com.originalDoc?.enabled,
  (enabled) => {
    if (enabled) api4com.webhookUrl.submit()
  },
  { immediate: true },
)

const crmUsers = computed(() =>
  (users.data?.crmUsers || []).filter((u) => u.name !== 'Administrator'),
)

const agents = createListResource({
  doctype: 'CRM Telephony Agent',
  fields: ['user', 'api4com_extension'],
  pageLength: 999,
  auto: true,
})

// user -> extension, kept in step with what was saved
const extensions = reactive({})
watch(
  () => agents.data,
  (rows) => {
    for (const row of rows || []) extensions[row.user] = row.api4com_extension
  },
  { immediate: true },
)

function enable() {
  api4com.doc.enabled = true
}

function disable() {
  api4com.doc.enabled = false
  update()
}

function update() {
  saveError.value = ''
  api4com.save.submit(null, {
    onSuccess: () => {
      api4com.reload()
      toast.success(__('API4Com settings saved'))
    },
    // e.g. API4Com refused the token: the settings are not saved
    onError: (err) => (saveError.value = err.messages?.[0] || err.message),
  })
}

function regenerate() {
  api4com.regenerateSecret.submit(null, {
    onSuccess: () => {
      confirmRegenerate.value = false
      // the server saved the settings: reload them, then the new address
      api4com.reload()
      api4com.webhookUrl.submit()
      toast.success(__('New secret generated and registered at API4Com'))
    },
    onError: (err) => toast.error(err.messages?.[0] || err.message),
  })
}

async function copyUrl() {
  await navigator.clipboard.writeText(webhookUrl.value)
  toast.success(__('Copied'))
}

async function saveExtension(user, value) {
  const previous = extensions[user] || ''
  if ((value || '').trim() === previous) return
  try {
    const result = await call(API + 'set_extension', {
      user,
      extension: value,
    })
    extensions[user] = result.extension
    toast.success(__('Extension saved'))
  } catch (err) {
    extensions[user] = previous
    toast.error(err.messages?.[0] || __('Something went wrong'))
  }
}

// Only what this page edits: the document methods (webhook address, new
// secret) answer with the document and would make it look unsaved
const isDirty = computed(() => {
  const doc = api4com.doc
  const original = api4com.originalDoc
  if (!doc || !original) return false
  return (
    Boolean(doc.enabled) !== Boolean(original.enabled) ||
    (doc.api_token || '') !== (original.api_token || '')
  )
})
</script>
