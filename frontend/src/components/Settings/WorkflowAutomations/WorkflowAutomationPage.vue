<template>
  <SettingsLayoutBase
    v-if="screen === 'list'"
    :title="__('Automation')"
    :description="__('Create workflow automations for CRM documents.')"
  >
    <template #header-top>
      <AutomationTabs current="workflow-automations" />
    </template>
    <template #header-actions>
      <Button
        :label="__('New automation')"
        variant="solid"
        icon-left="lucide-plus"
        @click="newAutomation"
      />
    </template>
    <template v-if="showSearch" #header-bottom>
      <div class="relative">
        <TextInput
          v-model="search"
          :placeholder="__('Search')"
          :debounce="300"
          class="rounded-4 border-outline-gray-2 bg-surface-gray-2"
        >
          <template #prefix>
            <span class="lucide-search size-4" aria-hidden="true" />
          </template>
        </TextInput>
        <Button
          v-if="search"
          icon="lucide-x"
          variant="ghost"
          class="absolute right-1 top-1/2 -translate-y-1/2"
          @click="search = ''"
        />
      </div>
    </template>
    <template #content>
      <div v-if="automations.list.loading" class="mt-10 flex justify-center">
        <LoadingIndicator class="w-4" />
      </div>
      <SettingsEmptyState
        v-else-if="!filteredAutomations.length"
        :icon="LucideWorkflow"
        :title="__('No workflow automations yet')"
        :description="
          __('Create automations to do repetitive tasks without effort.')
        "
        :action-label="__('New automation')"
        @action="newAutomation"
      />
      <!-- Figma "Configurações · Automação · Automações" (2335:9863) -->
      <div v-else class="ct-table">
        <div class="ct-table-head" :style="listColumns">
          <div>{{ __('Name') }}</div>
          <div>{{ __('Document') }}</div>
          <div>{{ __('Status') }}</div>
          <div>{{ __('Enabled', null, 'automation') }}</div>
          <div>{{ __('Created by') }}</div>
        </div>
        <div
          v-for="row in filteredAutomations"
          :key="row.name"
          class="ct-table-row cursor-pointer hover:bg-[var(--ct-bg-soft)]"
          :style="listColumns"
          @click="openAutomation(row)"
        >
          <div class="ct-table-name">{{ row.title || row.name }}</div>
          <div class="truncate">{{ formatDocType(row.document_type) }}</div>
          <div class="flex">
            <span
              class="ct-pill ct-pill-dot"
              :class="row.enabled && 'ct-pill-green'"
            >
              {{ row.enabled ? __('Active', null, 'automation') : __('Draft') }}
            </span>
          </div>
          <div class="flex" @click.stop>
            <Switch
              size="md"
              :model-value="Boolean(row.enabled)"
              :disabled="toggling.has(row.name)"
              :aria-label="__('Enabled')"
              @update:model-value="toggleAutomation(row, $event)"
            />
          </div>
          <div class="flex items-center justify-between gap-2" @click.stop>
            <span class="truncate">{{ ownerName(row.owner) }}</span>
            <Dropdown
              align="end"
              :options="rowOptions(row)"
              @update:open="(open) => open && (confirmingDelete = '')"
            >
              <Button
                icon="lucide-more-horizontal"
                variant="ghost"
                size="sm"
                class="ct-row-menu -my-1.5"
                :aria-label="__('Options')"
              />
            </Dropdown>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <WorkflowAutomationDetail
    v-else
    :automation-name="selectedAutomation"
    @edit="showBuilder = true"
    @back="backToList"
  />

  <!-- The builder overlays the settings dialog: wider, taller, and dismissable only
       through its own close button so a stray click can't drop unsaved steps. -->
  <Dialog v-model:open="showBuilder" size="6xl" bare :dismissible="false">
    <template #default>
      <div class="h-[calc(100vh_-_6rem)]">
        <WorkflowAutomationBuilder
          v-if="showBuilder"
          :automation-name="selectedAutomation"
          @update:dirty="dirty = $event"
          @close="requestClose"
          @saved="onSaved"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LucideWorkflow from '~icons/lucide/workflow'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import AutomationTabs from '@/components/Settings/AutomationTabs.vue'
import '@/components/Settings/settingsTable.css'
import WorkflowAutomationBuilder from './WorkflowAutomationBuilder.vue'
import WorkflowAutomationDetail from './WorkflowAutomationDetail.vue'
import { sessionStore } from '@/stores/session'
import { ConfirmDelete } from '@/utils'
import { createDialog } from '@/utils/dialogs'
import { usersStore } from '@/stores/users'
import { disableSettingModalOutsideClick } from '@/composables/settings'
import {
  Button,
  Dialog,
  Dropdown,
  LoadingIndicator,
  Switch,
  call,
  createListResource,
  toast,
} from 'frappe-ui'
import { computed, onUnmounted, reactive, ref, watch } from 'vue'

const { getUser } = usersStore()

const screen = ref('list')
const search = ref('')
const selectedAutomation = ref('')
const confirmingDelete = ref('')
const showBuilder = ref(false)
const dirty = ref(false)
const toggling = reactive(new Set())

// Figma column widths at 1440px (Nome 406, Documento 132, Situação 152,
// Ativada 102, Criada por 190), kept in proportion on other widths
const listColumns = {
  gridTemplateColumns:
    'minmax(0,406fr) minmax(0,132fr) minmax(0,152fr) minmax(0,102fr) minmax(0,190fr)',
}

// Figma "Criada por": the name, "Você" for the current user
const { user: currentUser } = sessionStore()
function ownerName(owner) {
  return owner === currentUser ? __('You') : getUser(owner).full_name
}

// While the builder is up, a click outside must not take the settings dialog with it.
watch(showBuilder, (open) => (disableSettingModalOutsideClick.value = open))
onUnmounted(() => (disableSettingModalOutsideClick.value = false))

const automations = createListResource({
  doctype: 'Automation Flow',
  fields: [
    'name',
    'title',
    'document_type',
    'owner',
    'enabled',
    'creation',
    'modified',
  ],
  cache: ['workflowAutomations'],
  orderBy: 'creation desc',
  pageLength: 99,
  auto: true,
})

// On the template, not the div inside it: a declared slot still renders the layout's padded
// wrapper, which leaves a gap where the search box would have been.
const showSearch = computed(() => search.value || automations.data?.length > 9)

const filteredAutomations = computed(() => {
  const rows = automations.data || []
  const matches = search.value ? rows.filter((row) => matchesSearch(row)) : rows
  return sortByNewestCreated(matches)
})

const DOC_TYPE_LABELS = {
  'CRM Deal': () => __('Card'),
  'CRM Lead': () => __('Card'),
  'CRM Organization': () => __('Organization'),
  Contact: () => __('Contact'),
  'CRM Task': () => __('Task'),
  Communication: () => __('Communication'),
}

function formatDocType(doctype) {
  if (!doctype) return __('Any document')
  return DOC_TYPE_LABELS[doctype] ? DOC_TYPE_LABELS[doctype]() : __(doctype)
}

function matchesSearch(row) {
  const query = search.value.toLowerCase()
  return [row.title, row.name, row.document_type, getUser(row.owner).full_name]
    .filter(Boolean)
    .some((value) => value.toLowerCase().includes(query))
}

function sortByNewestCreated(rows) {
  return [...rows].sort(compareCreatedDesc)
}

function compareCreatedDesc(a, b) {
  return compareDesc(a.creation, b.creation) || compareDesc(a.name, b.name)
}

function compareDesc(a, b) {
  return String(b || '').localeCompare(String(a || ''))
}

function newAutomation() {
  selectedAutomation.value = ''
  showBuilder.value = true
}

function openAutomation(automation) {
  selectedAutomation.value = automation.name
  screen.value = 'detail'
}

/** Closing the builder always lands back on the list, warning first about unsaved edits. */
function requestClose() {
  if (!dirty.value) return closeBuilder()
  createDialog({
    title: __('Unsaved changes'),
    message: __('You have unsaved changes. Do you wish to exit?'),
    size: 'sm',
    actions: [
      { label: __('Keep editing'), onClick: ({ close }) => close() },
      {
        label: __('Discard and exit'),
        variant: 'solid',
        theme: 'red',
        onClick: closeBuilder,
      },
    ],
  })
}

function closeBuilder({ close } = {}) {
  close?.()
  showBuilder.value = false
  dirty.value = false
  backToList()
}

function backToList() {
  selectedAutomation.value = ''
  screen.value = 'list'
  reloadList()
}

function onSaved(saved) {
  selectedAutomation.value = saved?.name || selectedAutomation.value
  reloadList()
}

function reloadList() {
  automations.reload()
}

async function toggleAutomation(automation, enabled) {
  if (toggling.has(automation.name)) return
  const previous = automation.enabled
  automation.enabled = enabled ? 1 : 0
  toggling.add(automation.name)
  try {
    await updateEnabled(automation)
    toast.success(__('Automation updated'))
  } catch (error) {
    automation.enabled = previous
    toast.error(error?.message || __('Could not update automation'))
  } finally {
    toggling.delete(automation.name)
  }
}

function updateEnabled(automation) {
  return call('frappe.client.set_value', {
    doctype: 'Automation Flow',
    name: automation.name,
    fieldname: 'enabled',
    value: automation.enabled,
  })
}

function rowOptions(automation) {
  return [
    {
      label: __('Duplicate'),
      icon: 'lucide-copy',
      onClick: () => duplicateAutomation(automation),
    },
    ...ConfirmDelete({
      isConfirmingDelete: computed({
        get: () => confirmingDelete.value === automation.name,
        set: (value) => (confirmingDelete.value = value ? automation.name : ''),
      }),
      onConfirmDelete: () => deleteAutomation(automation),
    }),
  ]
}

async function duplicateAutomation(automation) {
  try {
    const source = await call('frappe.client.get', {
      doctype: 'Automation Flow',
      name: automation.name,
    })
    await call('frappe.client.insert', { doc: copyOf(source) })
    toast.success(__('Automation duplicated'))
    reloadList()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not duplicate automation'))
  }
}

/** A copy starts disabled, so a half-reviewed flow never runs the moment it is saved. */
function copyOf(source) {
  return {
    ...withoutIdentity(source),
    doctype: 'Automation Flow',
    title: nextCopyTitle(source.title),
    enabled: 0,
    actions: (source.actions || []).map(withoutIdentity),
  }
}

const IDENTITY_FIELDS = [
  'name',
  'creation',
  'modified',
  'owner',
  'modified_by',
  'idx',
  'parent',
  'parentfield',
  'parenttype',
]

function withoutIdentity(row) {
  const copy = { ...row }
  IDENTITY_FIELDS.forEach((field) => delete copy[field])
  return copy
}

/** "Welcome lead sequence" -> "Welcome lead sequence (1)", skipping names already taken. */
function nextCopyTitle(title) {
  const taken = new Set((automations.data || []).map((row) => row.title))
  let index = 1
  while (taken.has(`${title} (${index})`)) index += 1
  return `${title} (${index})`
}

async function deleteAutomation(automation) {
  await call('frappe.client.delete', {
    doctype: 'Automation Flow',
    name: automation.name,
  })
  toast.success(__('Automation deleted'))
  confirmingDelete.value = ''
  reloadList()
}
</script>
