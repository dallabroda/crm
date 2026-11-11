<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <!-- Figma "Entrada de leads · Formulários de captura" (2336:10624) -->
    <SettingsTabs :tabs="leadIntakeTabs" active="lead-capture-forms" />
    <SettingsPageHeader :title="__('Lead intake')">
      <template #description>
        {{
          __(
            'Capture leads and deals from public forms you embed on your website.',
          )
        }}
      </template>
      <template #actions>
        <Button
          :label="__('New form')"
          icon-left="lucide-plus"
          variant="solid"
          @click="openCreate"
        />
      </template>
    </SettingsPageHeader>

    <!-- List -->
    <div class="flex h-full flex-col overflow-y-auto">
      <div
        v-if="forms.loading && !forms.data"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <SettingsEmptyState
        v-else-if="forms.data?.length === 0"
        :icon="LucideTextCursorInput"
        :title="__('No lead capture forms yet')"
        :description="
          __(
            'Create forms to receive contacts from your website straight into the CRM.',
          )
        "
        :action-label="__('New form')"
        @action="openCreate"
      />
      <!-- Figma "Tabela": 40px gray header, rows 10px/16px; "Situação" holds
           the status pill and the "Mais ações" button at the end -->
      <div
        v-else
        class="w-full overflow-hidden rounded-lg border border-[var(--ct-border)]"
      >
        <div
          class="flex h-10 items-center gap-4 border-b border-[var(--ct-border)] bg-[var(--ct-bg-soft)] px-4 text-xs font-medium text-ink-gray-6"
        >
          <div class="min-w-0 flex-1">{{ __('Form') }}</div>
          <div class="w-[198px] shrink-0">{{ __('Status') }}</div>
        </div>
        <template v-for="(form, i) in forms.data" :key="form.name">
          <div
            class="flex w-full items-center gap-4 px-4 py-2.5 hover:bg-surface-gray-2"
          >
            <div
              class="flex min-w-0 flex-1 cursor-pointer flex-col gap-0.5"
              @click="$emit('open', form.name)"
            >
              <div
                class="truncate text-[14px] font-medium leading-5 text-ink-gray-9"
              >
                {{ form.title }}
              </div>
              <div class="truncate text-xs text-ink-gray-6">
                /crm-form/{{ form.route }}
              </div>
            </div>
            <div class="flex w-[198px] shrink-0 items-center justify-between">
              <span
                class="rounded-full px-2.5 py-0.5 text-xs font-medium"
                :class="
                  form.published
                    ? 'bg-[var(--ct-success-soft)] text-[var(--ct-success)]'
                    : 'bg-[var(--ct-bg-panel)] text-ink-gray-9'
                "
              >
                {{ form.published ? __('Published') : __('Draft') }}
              </span>
              <Dropdown
                align="end"
                :options="rowOptions(form)"
                @update:open="(open) => open && (isConfirmingDelete = false)"
              >
                <Button icon="lucide-more-horizontal" variant="ghost" />
              </Dropdown>
            </div>
          </div>
          <div
            v-if="forms.data.length !== i + 1"
            class="h-px bg-[var(--ct-border)]"
          />
        </template>
      </div>
    </div>
  </div>

  <!-- create dialog -->
  <Dialog v-model:open="showCreate" :title="__('New form')">
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="draft.title"
          type="text"
          :label="__('Title')"
          :placeholder="__('Contact sales')"
          @input="onTitleInput"
        />
        <div>
          <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Route') }}</div>
          <div
            class="flex h-7 cursor-text items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base"
            @click="focusRouteEnd"
          >
            <span class="shrink-0 text-ink-gray-4">/crm-form/</span>
            <input
              v-model="draft.route"
              :placeholder="__('contact-sales')"
              class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
              @input="routeEdited = true"
            />
          </div>
        </div>
        <ErrorMessage v-if="createError" :message="createError" />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Create form')"
        :loading="creating"
        @click="createForm"
      />
    </template>
  </Dialog>
</template>

<script setup>
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsTabs from '@/components/Settings/SettingsTabs.vue'
import { leadIntakeTabs } from '@/components/Settings/LeadSyncing/webhookSourcesApi'
import {
  Button,
  Badge,
  Dropdown,
  Dialog,
  FormControl,
  ErrorMessage,
  LoadingIndicator,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, reactive } from 'vue'
import { ConfirmDelete, copyToClipboard } from '../../../utils'

const emit = defineEmits(['open'])
const { capture } = useTelemetry()

const isConfirmingDelete = ref(false)

const targetOptions = [
  { label: 'Lead', value: 'CRM Lead' },
  { label: 'Deal', value: 'CRM Deal' },
]
const docLabel = (dt) => targetOptions.find((o) => o.value === dt)?.label || dt

const forms = createResource({
  url: 'crm.api.form.list_forms',
  auto: true,
})

// create dialog: title, maps-to and route captured up front (maps-to governs
// which fields are available, so it's a first-class creation choice)
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const draft = reactive({ title: '', route: '', document_type: 'CRM Deal' })
let routeEdited = false

function slugify(v) {
  return (v || '')
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}
function openCreate() {
  draft.title = ''
  draft.route = ''
  draft.document_type = 'CRM Deal'
  routeEdited = false
  createError.value = ''
  showCreate.value = true
}
function onTitleInput(e) {
  if (!routeEdited) draft.route = slugify(e?.target?.value ?? draft.title)
}
// clicking the /crm-form/ prefix or box padding focuses the slug at the end
function focusRouteEnd(e) {
  if (e.target.tagName === 'INPUT') return
  const input = e.currentTarget.querySelector('input')
  if (!input) return
  input.focus()
  input.setSelectionRange(input.value.length, input.value.length)
}
async function createForm() {
  createError.value = ''
  const route = slugify(draft.route || draft.title)
  if (!draft.title || !route) {
    createError.value = __('Title and route are required')
    return
  }
  creating.value = true
  try {
    const doc = await call('crm.api.form.save_form', {
      name: null,
      form: { title: draft.title, route, document_type: draft.document_type },
    })
    capture('form_created', { doctype: draft.document_type })
    showCreate.value = false
    emit('open', doc.name)
    forms.reload()
    toast.success(__('Form created'))
  } catch (e) {
    createError.value =
      e?.messages?.[0] || e?.message || __('Could not create form')
  } finally {
    creating.value = false
  }
}

async function togglePublished(form, value) {
  try {
    await call('crm.api.form.set_published', {
      name: form.name,
      published: value ? 1 : 0,
    })
    form.published = value ? 1 : 0
    if (value) capture('form_published', { source: 'list' })
    toast.success(value ? __('Form published') : __('Form unpublished'))
  } catch (e) {
    forms.reload()
    toast.error(e?.messages?.[0] || __('Could not update form'))
  }
}

function copyLink(form) {
  copyToClipboard(`${window.location.origin}/crm-form/${form.route}`)
}

async function deleteForm(form) {
  await call('crm.api.form.delete_form', { name: form.name })
  forms.reload()
  toast.success(__('Form deleted'))
}

function rowOptions(form) {
  return [
    {
      label: __('Edit'),
      icon: 'lucide-edit-2',
      onClick: () => emit('open', form.name),
    },
    {
      label: form.published ? __('Unpublish') : __('Publish'),
      icon: form.published ? 'lucide-eye-off' : 'lucide-eye',
      onClick: () => togglePublished(form, !form.published),
    },
    {
      label: __('Copy link'),
      icon: 'lucide-link',
      onClick: () => copyLink(form),
    },
    ...ConfirmDelete({
      isConfirmingDelete,
      onConfirmDelete: () => deleteForm(form),
    }),
  ]
}

defineExpose({ reload: () => forms.reload() })
</script>
