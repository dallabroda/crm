<template>
  <SettingsLayoutBase
    :title="__('Automation')"
    :description="__('Manage your service level agreement policies.')"
  >
    <template #header-top>
      <AutomationTabs current="sla-policies" />
    </template>
    <template #header-actions>
      <Button
        :label="__('New policy')"
        variant="solid"
        icon-left="lucide-plus"
        @click="createNewSlaPolicy"
      />
    </template>
    <template
      v-if="slaPolicyListResource.data?.length > 9 || slaSearchQuery.length"
      #header-bottom
    >
      <div class="relative">
        <TextInput
          v-model="slaSearchQuery"
          :placeholder="__('Search')"
          type="text"
          class="bg-surface-gray-2 hover:bg-surface-gray-2 focus:ring-0 border-outline-gray-2 rounded-4"
          :debounce="300"
        >
          <template #prefix>
            <span class="lucide-search size-4" aria-hidden="true" />
          </template>
        </TextInput>
        <Button
          v-if="slaSearchQuery"
          icon="lucide-x"
          variant="ghost"
          class="absolute right-1 top-1/2 -translate-y-1/2"
          @click="slaSearchQuery = ''"
        />
      </div>
    </template>
    <template #content>
      <div
        v-if="
          slaPolicyListResource.list.loading && !slaPolicyListResource.list.data
        "
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="h-full">
        <SettingsEmptyState
          v-if="
            !slaPolicyListResource.list.loading &&
            !slaPolicyListResource.list.data?.length
          "
          :icon="LucideShieldCheck"
          :title="__('No SLA policies yet')"
          :description="
            __('Create policies to set response and resolution deadlines.')
          "
          :action-label="__('New policy')"
          @action="createNewSlaPolicy"
        />
        <!-- Figma "Configurações · Automação · Prazos (SLA)" (2335:10382) -->
        <div v-else class="ct-table">
          <div class="ct-table-head" :style="columns">
            <div>{{ __('Name') }}</div>
            <div>{{ __('Applies to') }}</div>
            <div>{{ __('First response') }}</div>
            <div>{{ __('Resolution') }}</div>
            <div>{{ __('Active', null, 'automation') }}</div>
          </div>
          <div
            v-for="sla in slaPolicyListResource.data"
            :key="sla.name"
            class="ct-table-row cursor-pointer hover:bg-[var(--ct-bg-soft)]"
            :style="columns"
            @click="updateStep('view', sla, true)"
          >
            <div class="flex items-center gap-2">
              <span class="ct-table-name">{{ sla.name }}</span>
              <span v-if="sla.default" class="ct-pill ct-pill-dot">
                {{ __('Default') }}
              </span>
            </div>
            <div class="truncate">
              {{
                hasCondition(sla)
                  ? __('Cards with a condition')
                  : __('All cards')
              }}
            </div>
            <div>
              {{ formatDuration(defaultPriority(sla)?.first_response_time) }}
            </div>
            <div>
              {{ formatDuration(defaultPriority(sla)?.resolution_time) }}
            </div>
            <div class="flex items-center justify-between gap-2" @click.stop>
              <Switch
                size="md"
                :modelValue="sla.enabled"
                @update:modelValue="onToggle(sla)"
              />
              <Dropdown
                align="end"
                :options="dropdownOptions(sla)"
                @update:open="(open) => open && (isConfirmingDelete = false)"
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
        <!-- one dialog for the list (it was repeated in every row) -->
        <Dialog
          v-model:open="duplicateDialog.show"
          :title="__('Duplicate SLA Policy')"
        >
          <template #default>
            <div class="flex flex-col gap-4">
              <FormControl
                v-model="duplicateDialog.name"
                :label="__('New SLA Policy Name')"
                type="text"
                maxlength="100"
              />
            </div>
          </template>
          <template #actions>
            <div class="flex gap-2 justify-end">
              <Button
                variant="subtle"
                :label="__('Close')"
                @click="duplicateDialog.show = false"
              />
              <Button
                variant="solid"
                :label="__('Duplicate')"
                @click="() => duplicate(duplicateDialog.sla)"
              />
            </div>
          </template>
        </Dialog>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import LucideShieldCheck from '~icons/lucide/shield-check'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import AutomationTabs from '@/components/Settings/AutomationTabs.vue'
import '@/components/Settings/settingsTable.css'
import {
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'
import { ConfirmDelete } from '@/utils'
import { resetSlaData } from './utils'
import { computed, inject, ref, watch } from 'vue'

const slaPolicyListResource = inject('slaPolicyListResource')
const updateStep = inject('updateStep')
const slaSearchQuery = inject('slaSearchQuery')

// Figma column widths at 1440px (Nome 224, Vale para 345, 1ª resposta 152,
// Resolução 152, Ativa 109), kept in proportion on other widths
const columns = {
  gridTemplateColumns:
    'minmax(0,224fr) minmax(0,345fr) minmax(0,152fr) minmax(0,152fr) minmax(0,109fr)',
}

// "1ª resposta" and "Resolução" of each policy: those of its default priority
const priorities = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Service Level Priority',
    parent: 'CRM Service Level Agreement',
    fields: [
      'parent',
      'default_priority',
      'first_response_time',
      'resolution_time',
    ],
    limit_page_length: 0,
  },
  cache: ['SLAPolicyPriorities'],
  auto: true,
})
const prioritiesBySla = computed(() => {
  let map = {}
  for (let row of priorities.data || []) {
    if (!map[row.parent] || row.default_priority) map[row.parent] = row
  }
  return map
})
function hasCondition(sla) {
  let json = sla.condition_json
  return Boolean(sla.condition || (json && json !== '[]'))
}
function defaultPriority(sla) {
  return prioritiesBySla.value[sla.name]
}
watch(
  () => slaPolicyListResource.data,
  () => priorities.reload(),
)

// seconds (Duration) → "30 minutos", "2 horas", "1 dia"
function formatDuration(seconds) {
  if (!seconds) return '—'
  let [value, one, many] =
    seconds % 86400 === 0
      ? [seconds / 86400, '1 day', '{0} days']
      : seconds % 3600 === 0
        ? [seconds / 3600, '1 hour', '{0} hours']
        : [Math.round(seconds / 60), '1 minute', '{0} minutes']
  return value === 1 ? __(one) : __(many, [value])
}

function createNewSlaPolicy() {
  resetSlaData()
  updateStep('view', null)
}

const duplicateDialog = ref({
  show: false,
  name: '',
})

const isConfirmingDelete = ref(false)

const dropdownOptions = (sla) => [
  {
    label: __('Duplicate'),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: sla.name + ' (Copy)',
        sla,
      }
    },
    icon: 'lucide-copy',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteSla(sla),
    isConfirmingDelete,
  }),
]

const duplicate = (sla) => {
  createResource({
    url: 'frappe.client.get',
    params: {
      doctype: 'CRM Service Level Agreement',
      name: sla.name,
    },
    onSuccess: (data) => {
      createResource({
        url: 'frappe.client.insert',
        params: {
          doc: {
            ...data,
            default: false,
            sla_name: duplicateDialog.value.name,
          },
        },
        auto: true,
        onSuccess(newSlaData) {
          slaPolicyListResource.reload()
          toast.success(__('SLA policy duplicated'))
          duplicateDialog.value = {
            show: false,
            name: '',
          }
          resetSlaData()
          setTimeout(() => {
            updateStep('view', newSlaData, true)
          }, 250)
        },
      })
    },
    auto: true,
  })
}

const deleteSla = (sla) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  slaPolicyListResource.delete.submit(sla.name, {
    onSuccess: () => {
      toast.success(__('SLA policy deleted'))
    },
    onError: (err) => {
      const message =
        err.messages?.[0] || __('Something went wrong, try again later')
      toast.error(message)
    },
  })
}

const onToggle = (sla) => {
  if (sla.default) {
    toast.error(__('An SLA set as default cannot be disabled'))
    return
  }
  slaPolicyListResource.setValue.submit(
    {
      name: sla.name,
      enabled: !sla.enabled,
    },
    {
      onSuccess: () => {
        toast.success(__('SLA policy status updated'))
      },
    },
  )
}

watch(slaSearchQuery, (newValue) => {
  slaPolicyListResource.filters = {
    name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    slaPolicyListResource.start = 0
    slaPolicyListResource.pageLength = 10
  }
  slaPolicyListResource.reload()
})
</script>
