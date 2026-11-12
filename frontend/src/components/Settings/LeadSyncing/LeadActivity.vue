<template>
  <!-- Figma "Últimos contatos recebidos": 16/500 title, bordered list -->
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="text-lg font-medium leading-6 text-ink-gray-9">
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
    <ul
      v-else
      class="flex flex-col overflow-hidden rounded-lg border border-[var(--ct-border-soft)]"
    >
      <li
        v-for="(item, i) in items"
        :key="i"
        class="flex items-center gap-3 border-b border-[var(--ct-border-soft)] px-4 py-2.5 text-base last:border-b-0"
        :class="item.card && 'cursor-pointer hover:bg-surface-gray-2'"
        @click="openCard(item)"
      >
        <!-- Figma "Pílula de status": Duplicar amber, Novo blue -->
        <span
          class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium"
          :class="statusClass(item.status)"
        >
          {{ statusLabel(item.status) }}
        </span>
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <span
            class="truncate text-[14px] font-medium leading-5 text-ink-gray-9"
          >
            {{ item.lead_name || __('Lead without name') }}
          </span>
          <span class="truncate text-[14px] leading-5 text-ink-gray-6">
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
          <span class="shrink-0 text-xs text-[var(--ct-text-tertiary)]">
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
import { Button, Tooltip, toast } from 'frappe-ui'
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

function statusClass(status) {
  return (
    {
      Created: 'bg-[var(--ct-accent-soft)] text-[var(--ct-accent)]',
      Duplicate: 'bg-[var(--ct-warning-soft)] text-[var(--ct-warning)]',
      Failed: 'bg-[var(--ct-danger-soft)] text-[var(--ct-danger)]',
      Test: 'bg-[var(--ct-accent-soft)] text-[var(--ct-accent)]',
    }[status] || 'bg-[var(--ct-bg-panel)] text-ink-gray-9'
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
