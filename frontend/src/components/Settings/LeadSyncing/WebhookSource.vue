<template>
  <div class="flex flex-col rounded border border-outline-gray-1">
    <div class="flex items-center gap-3 px-3 py-2">
      <span
        class="size-4 shrink-0 text-ink-gray-6"
        :class="type.icon"
        aria-hidden="true"
      />
      <div class="flex min-w-0 flex-1 flex-col">
        <span class="truncate text-sm text-ink-gray-8">
          {{ source.label || type.label }}
        </span>
        <span class="text-p-xs text-ink-gray-5">
          {{ type.label }} ·
          {{
            source.last_lead_at
              ? __('Last lead {0}', [timeAgo(source.last_lead_at)])
              : __('No leads yet')
          }}
        </span>
      </div>
      <div class="w-56">
        <PipelineSelect
          :label="''"
          :model-value="source.pipeline"
          :disabled="saving"
          @update:model-value="(pipeline) => save({ pipeline })"
        />
      </div>
      <Button
        :label="__('How to connect')"
        :icon-right="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
        variant="ghost"
        @click="open = !open"
      />
      <Tooltip :text="__('Receive leads from this source')">
        <Switch
          :model-value="Boolean(source.enabled)"
          :disabled="saving || !source.pipeline"
          @update:model-value="(enabled) => save({ enabled: enabled ? 1 : 0 })"
        />
      </Tooltip>
    </div>

    <div
      v-if="open || newKey"
      class="flex flex-col gap-3 border-t border-outline-gray-1 px-3 py-3"
    >
      <!-- address and key -->
      <div class="grid grid-cols-[8rem_1fr_auto] items-center gap-2 text-sm">
        <span class="text-ink-gray-6">{{ __('Address (URL)') }}</span>
        <code
          class="truncate rounded bg-surface-gray-2 px-2 py-1 text-ink-gray-8"
        >
          {{ source.url }}
        </code>
        <Button
          icon="lucide-copy"
          variant="ghost"
          :aria-label="__('Copy')"
          @click="copyToClipboard(source.url)"
        />
        <span class="text-ink-gray-6">{{ __('Key') }}</span>
        <code
          class="truncate rounded px-2 py-1"
          :class="
            newKey
              ? 'bg-surface-amber-1 text-ink-gray-9'
              : 'bg-surface-gray-2 text-ink-gray-5'
          "
        >
          {{ newKey || `••••••••${source.key_hint || ''}` }}
        </code>
        <Button
          v-if="newKey"
          icon="lucide-copy"
          variant="ghost"
          :aria-label="__('Copy')"
          @click="copyToClipboard(newKey)"
        />
        <span v-else />
      </div>
      <p v-if="newKey" class="text-p-sm text-ink-amber-7">
        {{
          __(
            'Copy the key now: for safety it is shown only this once. If you lose it, create a new one.',
          )
        }}
      </p>

      <!-- where to paste, per tool -->
      <ol
        class="flex list-decimal flex-col gap-1 pl-5 text-p-sm text-ink-gray-7"
      >
        <template v-if="source.type === 'google_ads'">
          <li>
            {{
              __(
                'In Google Ads, open the campaign, then Assets › Lead forms and edit the form.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'In "Lead delivery options", choose Webhook integration and paste the Address (URL) and the Key above.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'Click "Send test data": the test lead shows up in Latest leads below.',
              )
            }}
          </li>
        </template>
        <template v-else-if="source.type === 'typeform'">
          <li>
            {{
              __(
                'In Typeform, open the form, then Connect › Webhooks › Add a webhook and paste the Address (URL).',
              )
            }}
          </li>
          <li>
            {{
              __(
                'In the webhook settings, turn on Secret and paste the Key above.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'To know which campaign brought each lead, add the hidden fields utm_source, utm_medium, utm_campaign, utm_content and utm_term to the form.',
              )
            }}
          </li>
        </template>
        <template v-else-if="source.type === 'website'">
          <li>
            {{
              __(
                'Paste this line at the end of every page of the site, before the closing body tag (it keeps the campaign of whoever arrives from an ad):',
              )
            }}
            <div class="mt-1 flex items-start gap-2">
              <code
                class="flex-1 whitespace-pre-wrap break-all rounded bg-surface-gray-2 px-2 py-1 text-ink-gray-8"
                >{{ snippet }}</code
              >
              <Button
                icon="lucide-copy"
                variant="ghost"
                :aria-label="__('Copy')"
                @click="copyToClipboard(snippet)"
              />
            </div>
          </li>
          <li>
            {{
              __(
                'Add data-credhub to each form that should create leads. Fields named name, email, phone and company are recognized; the others go to the card notes.',
              )
            }}
          </li>
        </template>
        <template v-else>
          <li>
            {{
              __(
                'Send a POST with a JSON body to the Address (URL), with the Key in the X-CredHub-Key header.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'Recognized fields: name, email, phone, company, utm_source, utm_medium, utm_campaign, utm_content, utm_term, gclid, fbclid. The others go to the card notes.',
              )
            }}
          </li>
          <li>
            {{
              __(
                'In Zapier or Make, use the "Webhooks" action with these same settings.',
              )
            }}
          </li>
        </template>
      </ol>

      <div class="flex justify-between">
        <Button
          :label="
            confirmRemove ? __('Confirm removal') : __('Remove this source')
          "
          :theme="confirmRemove ? 'red' : 'gray'"
          variant="ghost"
          :loading="removing"
          @click="remove"
          @blur="confirmRemove = false"
        />
        <Button
          :label="confirmKey ? __('Confirm new key') : __('Create a new key')"
          :theme="confirmKey ? 'red' : 'gray'"
          :loading="saving"
          @click="regenerateKey"
          @blur="confirmKey = false"
        />
      </div>
      <p v-if="confirmKey" class="text-p-sm text-ink-red-6">
        {{
          __(
            'The current key stops working at once: the tool where it was pasted must get the new one.',
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import PipelineSelect from '@/components/Pipelines/PipelineSelect.vue'
import { sourceType, webhookSourcesApi } from './webhookSourcesApi'
import { copyToClipboard, timeAgo } from '@/utils'
import { Button, Switch, Tooltip, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  source: { type: Object, required: true },
  // shown right after the source is created; never stored
  initialKey: { type: String, default: '' },
})

const emit = defineEmits(['changed'])

const type = computed(() => sourceType(props.source.type))
const open = ref(Boolean(props.initialKey))
const newKey = ref(props.initialKey)
const saving = ref(false)
const removing = ref(false)
const confirmRemove = ref(false)
const confirmKey = ref(false)

const snippet = computed(
  () =>
    `<script src="${window.location.origin}/assets/cred_hub/js/lead-form.js" data-source="${props.source.name}" data-key="${newKey.value || __('YOUR-KEY')}" defer><` +
    '/script>',
)

async function save(values) {
  saving.value = true
  try {
    await webhookSourcesApi.update(props.source.name, values)
    toast.success(__('Saved'))
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the source'))
  } finally {
    saving.value = false
  }
}

async function regenerateKey() {
  if (!confirmKey.value) {
    confirmKey.value = true
    return
  }
  confirmKey.value = false
  saving.value = true
  try {
    newKey.value = (
      await webhookSourcesApi.regenerateKey(props.source.name)
    ).key
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not create a new key'))
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!confirmRemove.value) {
    confirmRemove.value = true
    return
  }
  confirmRemove.value = false
  removing.value = true
  try {
    await webhookSourcesApi.remove(props.source.name)
    toast.success(__('Source removed. Its leads stop arriving.'))
    emit('changed')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not remove the source'))
  } finally {
    removing.value = false
  }
}
</script>
