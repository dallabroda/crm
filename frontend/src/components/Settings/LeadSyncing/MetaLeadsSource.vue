<template>
  <div class="flex flex-col gap-4 rounded-lg border border-outline-gray-2 p-4">
    <div class="flex items-start justify-between gap-4">
      <div class="flex items-start gap-3">
        <FacebookIcon class="mt-0.5 size-6 shrink-0" />
        <div class="flex flex-col gap-1">
          <div class="text-base-semibold text-ink-gray-9">
            {{ __('Facebook and Instagram lead ads') }}
          </div>
          <p class="text-p-sm text-ink-gray-6">
            <template v-if="connection.connected">
              {{ __('Connected as {0}', [connection.user_name]) }}
            </template>
            <template v-else>
              {{
                __(
                  'Connect the Facebook account that manages the page of your ads. Leads from its forms land in the funnel within seconds.',
                )
              }}
            </template>
          </p>
        </div>
      </div>
      <div class="flex shrink-0 gap-2">
        <template v-if="connection.connected">
          <Button
            :label="__('Add pages')"
            :loading="connecting"
            @click="connect"
          />
          <Button
            :label="
              confirmDisconnect ? __('Confirm disconnect') : __('Disconnect')
            "
            :theme="confirmDisconnect ? 'red' : 'gray'"
            :loading="disconnecting"
            @click="disconnect"
            @blur="confirmDisconnect = false"
          />
        </template>
        <Button
          v-else
          variant="solid"
          :label="__('Connect with Facebook')"
          :loading="connecting || loading"
          @click="connect"
        />
      </div>
    </div>

    <div
      v-if="connection.error"
      class="flex items-center justify-between gap-4 rounded bg-surface-red-1 px-3 py-2 text-p-sm text-ink-red-7"
    >
      <span>
        {{
          __(
            'The connection with Facebook stopped working, so new leads are not arriving. Connect again.',
          )
        }}
      </span>
      <Button
        :label="__('Connect again')"
        :loading="connecting"
        @click="connect"
      />
    </div>

    <template v-if="connection.connected">
      <p v-if="!connection.pages?.length" class="text-p-sm text-ink-gray-6">
        {{
          __(
            'No page with lead forms was shared with Cred Hub. Use "Add pages" and select the pages of your ads.',
          )
        }}
      </p>
      <div
        v-for="page in connection.pages"
        :key="page.id"
        class="flex flex-col gap-2"
      >
        <div class="text-sm font-medium text-ink-gray-8">{{ page.name }}</div>
        <p v-if="!page.forms?.length" class="text-p-sm text-ink-gray-5">
          {{ __('This page has no lead forms yet.') }}
        </p>
        <MetaLeadForm
          v-for="form in page.forms"
          :key="form.id"
          :form="form"
          @changed="load"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import FacebookIcon from '@/components/Icons/FacebookIcon.vue'
import MetaLeadForm from './MetaLeadForm.vue'
import { metaLeadsApi } from './metaLeadsApi'
import { Button, toast } from 'frappe-ui'
import { onBeforeUnmount, onMounted, ref } from 'vue'

const emit = defineEmits(['changed'])

const connection = ref({ connected: false, pages: [] })
const loading = ref(false)
const connecting = ref(false)
const disconnecting = ref(false)
const confirmDisconnect = ref(false)
let popupTimer = null

async function load() {
  loading.value = true
  try {
    connection.value = (await metaLeadsApi.getConnection()) || {
      connected: false,
      pages: [],
    }
  } catch (e) {
    toast.error(
      e?.messages?.[0] || __('Could not load the Facebook connection'),
    )
  } finally {
    loading.value = false
  }
  emit('changed')
}

// Facebook login runs in a popup on Cred Hub's central site, which closes it
// when the connection is saved; then the pages and forms are read again.
async function connect() {
  connecting.value = true
  try {
    let { auth_url } = await metaLeadsApi.startConnect()
    let popup = window.open(
      auth_url,
      'credhub-facebook',
      'width=600,height=720',
    )
    if (!popup) {
      // popup blocked: same flow in this tab, the central site sends it back here
      window.location.href = auth_url
      return
    }
    clearInterval(popupTimer)
    popupTimer = setInterval(() => {
      if (!popup.closed) return
      clearInterval(popupTimer)
      connecting.value = false
      load()
    }, 1000)
  } catch (e) {
    connecting.value = false
    toast.error(
      e?.messages?.[0] || __('Could not start the Facebook connection'),
    )
  }
}

async function disconnect() {
  if (!confirmDisconnect.value) {
    confirmDisconnect.value = true
    return
  }
  confirmDisconnect.value = false
  disconnecting.value = true
  try {
    await metaLeadsApi.disconnect()
    toast.success(__('Facebook disconnected. New leads stop arriving.'))
    await load()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not disconnect Facebook'))
  } finally {
    disconnecting.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => clearInterval(popupTimer))
</script>
