<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Email Templates')">
      <template #description>
        {{
          __(
            'Add, edit, and manage email templates for various CRM communications.',
          )
        }}
      </template>
      <template #actions>
        <Button
          :label="__('New Template')"
          icon-left="lucide-plus"
          variant="solid"
          @click="emit('updateStep', 'new-template')"
        />
      </template>
    </SettingsPageHeader>

    <!-- loading state -->
    <div
      v-if="templates.loading"
      class="flex mt-28 justify-between w-full h-full"
    >
      <Button
        :loading="templates.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <SettingsEmptyState
      v-else-if="!templates.loading && !templates.data?.length"
      :icon="LucideBuilding2"
      :title="__('No email templates yet')"
      :description="
        __(
          'Create templates to reply faster and keep your messages consistent.',
        )
      "
      :action-label="__('New Template')"
      @action="emit('updateStep', 'new-template')"
    />

    <!-- Email template list -->
    <div
      v-if="!templates.loading && templates.data?.length"
      class="flex flex-col overflow-hidden"
    >
      <div
        v-if="templates.data?.length > 10"
        class="flex items-center justify-between mb-4 pt-0.5"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search Template')"
          class="w-1/3"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <FormControl
          v-model="currentDoctype"
          type="select"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Deal'), value: 'CRM Deal' },
          ]"
        />
      </div>
      <div
        class="flex h-10 items-center rounded-t-lg border border-outline-gray-1 bg-surface-gray-2 px-4 text-xs font-medium text-ink-gray-6"
      >
        <div class="w-4/6">{{ __('Template Name') }}</div>
        <div class="w-1/6">{{ __('For') }}</div>
        <div class="w-1/6">{{ __('Enabled') }}</div>
      </div>
      <ul
        class="overflow-y-auto rounded-b-lg border border-t-0 border-outline-gray-1"
      >
        <template v-for="(template, i) in templatesList" :key="template.name">
          <li
            class="flex min-h-14 items-center justify-between px-4 py-2 cursor-pointer hover:bg-surface-gray-2"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div class="flex flex-col w-4/6 pr-5">
              <div class="text-base text-ink-gray-9 truncate">
                {{ template.name }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{ template.subject }}
              </div>
            </div>
            <div class="text-base text-ink-gray-6 w-1/6">
              {{ template.reference_doctype.replace('CRM ', '') }}
            </div>
            <div class="flex items-center justify-between w-1/6">
              <Switch
                v-model="template.enabled"
                size="sm"
                @update:model-value="
                  (val) => toggleEmailTemplate(template, val)
                "
                @click.stop
              />
              <Dropdown
                class=""
                :options="getDropdownOptions(template)"
                align="end"
                :button="{
                  icon: 'lucide-more-horizontal',
                  variant: 'ghost',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmDelete = false
                  },
                }"
                @click.stop
              />
            </div>
          </li>
          <div
            v-if="templatesList.length !== i + 1"
            class="h-px bg-outline-gray-1"
          />
        </template>
        <!-- Load More Button -->
        <div
          v-if="!templates.loading && templates.hasNextPage"
          class="flex justify-center"
        >
          <Button
            class="mt-3.5 p-2"
            :loading="templates.loading"
            :label="__('Load More')"
            icon-left="lucide-refresh-cw"
            @click="() => templates.next()"
          />
        </div>
      </ul>
    </div>
  </div>
</template>
<script setup>
import LucideBuilding2 from '~icons/lucide/building-2'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import { useBroadcast } from '@/composables/useBroadcast'
import { TextInput, FormControl, Switch, Dropdown, toast } from 'frappe-ui'
import { ref, computed, inject } from 'vue'
import { ConfirmDelete } from '../../../utils'

const emit = defineEmits(['updateStep'])

const { send } = useBroadcast()

const templates = inject('templates')

const search = ref('')
const currentDoctype = ref('All')
const confirmDelete = ref(false)

const templatesList = computed(() => {
  let list = templates.data || []
  if (search.value) {
    list = list.filter(
      (template) =>
        template.name.toLowerCase().includes(search.value.toLowerCase()) ||
        template.subject.toLowerCase().includes(search.value.toLowerCase()),
    )
  }
  if (currentDoctype.value !== 'All') {
    list = list.filter(
      (template) => template.reference_doctype === currentDoctype.value,
    )
  }
  return list
})

function toggleEmailTemplate(template, enabledVal) {
  templates.setValue.submit(
    {
      name: template.name,
      enabled: enabledVal ? 1 : 0,
    },
    {
      onSuccess: () => {
        toast.success(
          enabledVal
            ? __('Template enabled successfully')
            : __('Template disabled successfully'),
        )
        send('refresh-email-templates')
      },
      onError: (error) => {
        toast.error(error.messages[0] || __('Failed to update template'))
        // Revert the change if there was an error
        template.enabled = !enabledVal
      },
    },
  )
}

function deleteTemplate(template) {
  confirmDelete.value = false
  templates.delete.submit(template.name, {
    onSuccess: () => {
      toast.success(__('Template deleted successfully'))
    },
    onError: (error) => {
      toast.error(error.messages[0] || __('Failed to delete template'))
    },
  })
}

function getDropdownOptions(template) {
  let options = [
    {
      label: __('Duplicate'),
      icon: 'lucide-copy',
      onClick: () => emit('updateStep', 'new-template', { ...template }),
    },
    ...ConfirmDelete({
      onConfirmDelete: () => deleteTemplate(template),
      isConfirmingDelete: confirmDelete,
    }),
  ]

  return options
}
</script>
