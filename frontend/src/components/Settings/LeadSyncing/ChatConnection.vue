<template>
  <div class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4">
    <div class="flex items-start justify-between gap-4">
      <div class="flex items-start gap-3">
        <WhatsAppIcon class="mt-0.5 size-6 shrink-0" />
        <div class="flex flex-col gap-1">
          <div class="text-base-semibold text-ink-gray-9">
            {{ __('WhatsApp welcome message') }}
          </div>
          <p class="text-p-sm text-ink-gray-6">
            <template v-if="chat.connected">
              {{ __('Connected to the Cred Chat account {0}', [accountLabel]) }}
            </template>
            <template v-else>
              {{
                __(
                  'Connect your Cred Chat to send a WhatsApp message to each new lead the moment it arrives. Then turn it on in each source above.',
                )
              }}
            </template>
          </p>
        </div>
      </div>
      <Button
        v-if="chat.connected"
        :label="confirmDisconnect ? __('Confirm disconnect') : __('Disconnect')"
        :theme="confirmDisconnect ? 'red' : 'gray'"
        :loading="busy"
        @click="disconnect"
        @blur="confirmDisconnect = false"
      />
    </div>

    <div
      v-if="chat.error"
      class="rounded bg-surface-red-1 px-3 py-2 text-p-sm text-ink-red-7"
    >
      {{ chat.error }}
    </div>

    <p v-if="confirmDisconnect" class="text-p-sm text-ink-red-6">
      {{
        __(
          'The welcome message is turned off on every source and the access key is erased.',
        )
      }}
    </p>

    <template v-if="!chat.connected">
      <ol
        class="flex list-decimal flex-col gap-1 pl-5 text-p-sm text-ink-gray-7"
      >
        <li>
          {{
            __(
              'In Cred Chat, the account number is the number after /accounts/ in the address bar.',
            )
          }}
        </li>
        <li>
          {{
            __(
              'The access key is in Cred Chat › Profile settings › Access token. Use the key of an administrator of the account.',
            )
          }}
        </li>
      </ol>
      <div class="flex items-end gap-3">
        <div class="w-40">
          <FormControl
            v-model="accountId"
            type="number"
            :label="__('Account number')"
          />
        </div>
        <div class="flex-1">
          <FormControl
            v-model="accessToken"
            type="password"
            :label="__('Access key')"
            autocomplete="off"
          />
        </div>
        <Button
          variant="solid"
          :label="__('Connect')"
          :disabled="!accountId || !accessToken.trim()"
          :loading="busy"
          @click="connect"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { chat, loadChat, welcomeApi } from './welcomeApi'
import { Button, FormControl, toast } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const accountId = ref('')
const accessToken = ref('')
const busy = ref(false)
const confirmDisconnect = ref(false)

const accountLabel = computed(
  () => chat.account_name || `#${chat.account_id || ''}`,
)

async function load() {
  try {
    await loadChat()
  } catch (e) {
    toast.error(
      e?.messages?.[0] || __('Could not load the Cred Chat connection'),
    )
  }
}

async function connect() {
  busy.value = true
  try {
    Object.assign(
      chat,
      await welcomeApi.connect(accountId.value, accessToken.value.trim()),
    )
    accessToken.value = ''
    toast.success(__('Cred Chat connected'))
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not connect the Cred Chat'))
  } finally {
    busy.value = false
  }
}

async function disconnect() {
  if (!confirmDisconnect.value) {
    confirmDisconnect.value = true
    return
  }
  confirmDisconnect.value = false
  busy.value = true
  try {
    Object.assign(chat, await welcomeApi.disconnect())
    toast.success(__('Cred Chat disconnected. No welcome message is sent.'))
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not disconnect the Cred Chat'))
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
