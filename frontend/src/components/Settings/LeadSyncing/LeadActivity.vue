<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between">
      <div class="text-base-semibold text-ink-gray-9">
        {{ __('Latest leads') }}
      </div>
      <Button
        icon="lucide-refresh-cw"
        variant="ghost"
        :loading="loading"
        :aria-label="__('Reload')"
        @click="load"
      />
    </div>
    <p v-if="!loading && !items.length" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'No leads received yet. They show up here as soon as someone fills in a connected form.',
        )
      }}
    </p>
    <ul v-else class="flex flex-col">
      <li
        v-for="(item, i) in items"
        :key="i"
        class="flex items-center gap-3 border-b border-outline-gray-1 px-1 py-2 text-sm last:border-b-0"
        :class="item.card && 'cursor-pointer hover:bg-surface-gray-2'"
        @click="openCard(item)"
      >
        <Badge
          :label="statusLabel(item.status)"
          :theme="statusTheme(item.status)"
          variant="subtle"
        />
        <div class="flex min-w-0 flex-1 flex-col">
          <span class="truncate text-ink-gray-8">
            {{ item.lead_name || __('Lead without name') }}
          </span>
          <span class="truncate text-p-xs text-ink-gray-5">
            <template v-if="item.status === 'Failed'">{{
              item.error
            }}</template>
            <template v-else>
              {{ item.form_name || item.source_label }}
              <template v-if="item.assigned_to">
                · {{ __('assigned to {0}', [item.assigned_to]) }}
              </template>
            </template>
          </span>
        </div>
        <!-- WhatsApp welcome message: Sent means handed to Cred Chat -->
        <Tooltip
          v-if="item.welcome"
          :text="
            item.welcome === 'Failed'
              ? item.welcome_error
              : item.welcome === 'Sent'
                ? __('Open the conversation in Cred Chat')
                : __('Waiting to be sent')
          "
        >
          <a
            v-if="item.welcome === 'Sent' && item.welcome_url"
            :href="item.welcome_url"
            target="_blank"
            rel="noopener"
            class="flex shrink-0 items-center gap-1 text-p-xs text-ink-green-7 hover:underline"
            @click.stop
          >
            <span class="lucide-message-circle size-3.5" aria-hidden="true" />
            {{ __('Welcome sent') }}
          </a>
          <span
            v-else
            class="flex shrink-0 items-center gap-1 text-p-xs"
            :class="
              item.welcome === 'Failed' ? 'text-ink-red-6' : 'text-ink-gray-5'
            "
          >
            <span class="lucide-message-circle size-3.5" aria-hidden="true" />
            {{
              item.welcome === 'Failed'
                ? __('Welcome not sent')
                : item.welcome === 'Sent'
                  ? __('Welcome sent')
                  : __('Welcome queued')
            }}
          </span>
        </Tooltip>
        <Tooltip :text="formatDate(item.time)">
          <span class="shrink-0 text-p-xs text-ink-gray-5">
            {{ timeAgo(item.time) }}
          </span>
        </Tooltip>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { metaLeadsApi } from './metaLeadsApi'
import { formatDate, timeAgo } from '@/utils'
import { Badge, Button, Tooltip, toast } from 'frappe-ui'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSettings } from '@/composables/settings'

const router = useRouter()
const items = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    items.value = (await metaLeadsApi.getActivity()) || []
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the latest leads'))
  } finally {
    loading.value = false
  }
}

function statusLabel(status) {
  return (
    {
      Created: __('New'),
      Duplicate: __('Duplicate'),
      Failed: __('Failed'),
      Test: __('Test'),
    }[status] || status
  )
}

function statusTheme(status) {
  return (
    { Created: 'green', Duplicate: 'orange', Failed: 'red', Test: 'blue' }[
      status
    ] || 'gray'
  )
}

// card: { doctype: 'CRM Lead' | 'CRM Deal', name }
function openCard(item) {
  if (!item.card) return
  let isDeal = item.card.doctype === 'CRM Deal'
  showSettings.value = false
  router.push(
    isDeal
      ? { name: 'Deal', params: { dealId: item.card.name } }
      : { name: 'Lead', params: { leadId: item.card.name } },
  )
}

onMounted(load)
defineExpose({ load })
</script>
