<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between gap-4 px-2 pt-2">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('API') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Keys for other systems to read and write your cards, contacts and organizations. Each key only reaches the funnels you choose and does not take a user seat.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="data"
        variant="solid"
        icon-left="plus"
        :label="__('New key')"
        :disabled="activeCount >= data.limit"
        @click="openForm()"
      />
    </div>

    <div v-if="!data" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="apiKeys.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <div v-else class="flex flex-col gap-4 overflow-y-auto px-2">
      <!-- Old keys (token of a user, made in the technical screen) stop on a date set on deploy -->
      <div
        v-if="data.legacy_until && data.legacy_users.length"
        class="rounded px-4 py-3 text-p-base"
        :class="
          legacyStopped(data.legacy_until)
            ? 'bg-surface-red-1 text-ink-red-7'
            : 'bg-surface-amber-1 text-ink-amber-7'
        "
      >
        <p class="text-base-semibold">
          {{
            legacyStopped(data.legacy_until)
              ? __('The old API keys stopped on {0}.', [
                  dayMonth(data.legacy_until),
                ])
              : __('The old API keys stop on {0}.', [
                  dayMonth(data.legacy_until),
                ])
          }}
        </p>
        <p class="mt-1 text-p-sm">
          {{
            __(
              'Create a key here for each integration and replace it in the system that uses it. Users with an old key: {0}.',
              [data.legacy_users.map((u) => u.full_name || u.name).join(', ')],
            )
          }}
        </p>
      </div>

      <p v-if="activeCount >= data.limit" class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Your company can have up to {0} active keys. Revoke one to create another.',
            [data.limit],
          )
        }}
      </p>

      <div
        v-if="!data.keys.length"
        class="rounded border border-outline-gray-1 px-4 py-6 text-center text-p-base text-ink-gray-6"
      >
        {{ __('No API keys yet.') }}
      </div>

      <div
        v-for="key in data.keys"
        :key="key.name"
        class="flex flex-col gap-2 rounded border border-outline-gray-1 p-4"
        :class="{ 'opacity-60': key.status !== 'Active' }"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex flex-col gap-0.5">
            <div class="flex items-center gap-2">
              <span class="text-base-semibold text-ink-gray-9">
                {{ key.label }}
              </span>
              <Badge
                :label="key.status === 'Active' ? __('In use') : __('Revoked')"
                :theme="key.status === 'Active' ? 'green' : 'gray'"
                variant="subtle"
              />
            </div>
            <span class="font-mono text-p-sm text-ink-gray-6">
              {{ key.prefix }}_…{{ key.secret_hint }}
            </span>
          </div>
          <div v-if="key.status === 'Active'" class="flex gap-2">
            <Button :label="__('Edit')" @click="openForm(key)" />
            <Button
              :label="
                confirm.rotate === key.name
                  ? __('Confirm new secret')
                  : __('New secret')
              "
              :theme="confirm.rotate === key.name ? 'red' : 'gray'"
              :loading="busy === key.name + ':rotate'"
              @click="rotate(key)"
              @blur="confirm.rotate = null"
            />
            <Button
              :label="
                confirm.revoke === key.name
                  ? __('Confirm revoke')
                  : __('Revoke')
              "
              :theme="confirm.revoke === key.name ? 'red' : 'gray'"
              :loading="busy === key.name + ':revoke'"
              @click="revoke(key)"
              @blur="confirm.revoke = null"
            />
          </div>
        </div>
        <p v-if="confirm.rotate === key.name" class="text-p-sm text-ink-red-6">
          {{ __('The current secret stops working right away.') }}
        </p>
        <p v-if="confirm.revoke === key.name" class="text-p-sm text-ink-red-6">
          {{ __('The key stops working right away. This cannot be undone.') }}
        </p>
        <div class="flex flex-wrap gap-x-6 gap-y-1 text-p-sm text-ink-gray-6">
          <span>{{ __('Permissions: {0}', [scopeLabels(key.scopes)]) }}</span>
          <span v-if="key.pipelines.length">
            {{ __('Funnels: {0}', [pipelineLabels(key.pipelines)]) }}
          </span>
          <span v-if="key.allowed_ips">
            {{ __('IPs: {0}', [key.allowed_ips.split('\n').join(', ')]) }}
          </span>
          <span v-if="key.expires_on">
            {{ __('Valid until {0}', [formatDate(key.expires_on, '', true)]) }}
          </span>
          <span>
            {{
              key.last_used_on
                ? __('Last used {0} from {1}', [
                    formatDate(key.last_used_on),
                    key.last_used_ip,
                  ])
                : __('Never used')
            }}
          </span>
          <span>
            {{
              __('Created by {0} on {1}', [
                key.created_by,
                formatDate(key.created_on, '', true),
              ])
            }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Create / edit -->
  <Dialog
    v-model:open="form.show"
    :title="form.name ? __('Edit API key') : __('New API key')"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="form.label"
          :label="__('Name')"
          :placeholder="__('e.g. ERP, website, data warehouse')"
          type="text"
        />
        <div class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">{{ __('Permissions') }}</span>
          <div
            v-for="row in SCOPE_ROWS"
            :key="row.label"
            class="flex items-center justify-between gap-4 text-p-base"
          >
            <span>{{ __(row.label) }}</span>
            <div class="flex gap-4">
              <FormControl
                v-if="row.read"
                v-model="form.scopes[row.read]"
                type="checkbox"
                :label="__('Read')"
              />
              <FormControl
                v-if="row.write"
                v-model="form.scopes[row.write]"
                type="checkbox"
                :label="__(row.writeLabel || 'Write')"
              />
            </div>
          </div>
          <FormControl
            v-model="form.scopes[ADMIN_SCOPE]"
            type="checkbox"
            :label="__('Fields and rules of the stages (admin)')"
          />
          <p v-if="form.scopes[ADMIN_SCOPE]" class="text-p-sm text-ink-amber-7">
            {{
              __(
                'The key can change which fields the chosen funnels use and the rules of each stage (visible, required, read-only).',
              )
            }}
          </p>
        </div>
        <div v-if="needsPipelines(selectedScopes)" class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">{{ __('Funnels') }}</span>
          <FormControl
            v-for="p in pipelines.pipelines"
            :key="p.name"
            v-model="form.pipelines[p.name]"
            type="checkbox"
            :label="p.pipeline_name"
          />
        </div>
        <FormControl
          v-model="form.allowed_ips"
          :label="__('Allowed IPs (optional)')"
          :placeholder="__('One IP address or range per line')"
          type="textarea"
        />
        <FormControl
          v-model="form.expires_on"
          :label="__('Valid until (optional)')"
          type="date"
        />
        <ErrorMessage :message="form.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="form.show = false"
        />
        <Button
          variant="solid"
          :label="form.name ? __('Save') : __('Create key')"
          :loading="busy === 'form'"
          @click="save"
        />
      </div>
    </template>
  </Dialog>

  <!-- The secret, once -->
  <Dialog v-model:open="secret.show" :title="__('Copy the key now')">
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">{{ secretHelp }}</p>
        <div
          class="break-all rounded bg-surface-gray-2 px-3 py-2 font-mono text-p-sm text-ink-gray-9"
        >
          {{ secret.token }}
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          :label="__('Copy')"
          icon-left="copy"
          @click="copyToClipboard(secret.token)"
        />
        <Button variant="solid" :label="__('Done')" @click="closeSecret" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { pipelinesStore } from '@/stores/pipelines'
import { copyToClipboard, formatDate } from '@/utils'
import { apiKeys, apiKeysApi, loadApiKeys } from './apiKeysApi'
import {
  ADMIN_SCOPE,
  SCOPE_ROWS,
  cleanIps,
  dayMonth,
  legacyStopped,
  needsPipelines,
} from './apiKeysUtils'

const pipelines = pipelinesStore()
const data = computed(() => apiKeys.data)
const activeCount = computed(
  () => (data.value?.keys || []).filter((k) => k.status === 'Active').length,
)
const busy = ref(null)
const confirm = reactive({ rotate: null, revoke: null })
const form = reactive({
  show: false,
  name: null,
  label: '',
  scopes: {},
  pipelines: {},
  allowed_ips: '',
  expires_on: '',
  error: '',
})
const secret = reactive({ show: false, token: '' })
// In the script: "<key>" inside the template would read as an HTML tag
const secretHelp = __(
  'This is the only time the key is shown. Store it in the system that will use it, sent as the header "Authorization: Bearer <key>".',
)

const selectedScopes = computed(() =>
  Object.keys(form.scopes).filter((s) => form.scopes[s]),
)

onMounted(() => {
  loadApiKeys()
  pipelines.ensureLoaded()
})

function scopeLabels(scopes) {
  let labels = Object.fromEntries(
    (data.value?.scopes || []).map((s) => [s.value, s.label]),
  )
  return scopes.map((s) => labels[s] || s).join(', ')
}

function pipelineLabels(names) {
  return names
    .map((n) => pipelines.getPipeline(n)?.pipeline_name || n)
    .join(', ')
}

function openForm(key = null) {
  Object.assign(form, {
    show: true,
    name: key?.name || null,
    label: key?.label || '',
    scopes: Object.fromEntries((key?.scopes || []).map((s) => [s, true])),
    pipelines: Object.fromEntries((key?.pipelines || []).map((p) => [p, true])),
    allowed_ips: key?.allowed_ips || '',
    expires_on: key?.expires_on || '',
    error: '',
  })
}

function errorText(e) {
  return (
    e?.messages?.[0] || e?.message || __('Something went wrong. Try again.')
  )
}

async function save() {
  let values = {
    label: form.label,
    scopes: selectedScopes.value,
    pipelines: needsPipelines(selectedScopes.value)
      ? Object.keys(form.pipelines).filter((p) => form.pipelines[p])
      : [],
    allowed_ips: cleanIps(form.allowed_ips),
    expires_on: form.expires_on || '',
  }
  busy.value = 'form'
  form.error = ''
  try {
    if (form.name) {
      await apiKeysApi.update(form.name, values)
      toast.success(__('Key saved'))
    } else {
      let created = await apiKeysApi.create(values)
      showSecret(created.token)
    }
    form.show = false
    await loadApiKeys()
  } catch (e) {
    form.error = errorText(e)
  } finally {
    busy.value = null
  }
}

async function rotate(key) {
  if (confirm.rotate !== key.name) {
    confirm.rotate = key.name
    return
  }
  confirm.rotate = null
  busy.value = key.name + ':rotate'
  try {
    let rotated = await apiKeysApi.rotate(key.name)
    showSecret(rotated.token)
    await loadApiKeys()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = null
  }
}

async function revoke(key) {
  if (confirm.revoke !== key.name) {
    confirm.revoke = key.name
    return
  }
  confirm.revoke = null
  busy.value = key.name + ':revoke'
  try {
    await apiKeysApi.revoke(key.name)
    toast.success(__('Key revoked'))
    await loadApiKeys()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = null
  }
}

function showSecret(token) {
  Object.assign(secret, { show: true, token })
}

function closeSecret() {
  secret.show = false
}

// However the dialog closes, the token leaves the page: it cannot be shown again
watch(
  () => secret.show,
  (open) => {
    if (!open) secret.token = ''
  },
)
</script>
