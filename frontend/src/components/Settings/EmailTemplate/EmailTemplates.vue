<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <!-- Figma "E-mail · Modelos" (2336:10373): tab Modelos of the "E-mail" page -->
    <SettingsSectionTabs :tabs="emailTabs" active="email-templates" />
    <SettingsPageHeader :title="__('Email')">
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
      :icon="LucideFileText"
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
      <!-- Figma "Tabela": Nome, Assunto, Usado em, Ativo; 40px gray header,
           rows 10px/16px with 16px between the cells -->
      <div
        class="flex h-10 items-center gap-4 rounded-t-lg border border-[var(--ct-border)] bg-[var(--ct-bg-soft)] px-4 text-xs font-medium text-ink-gray-6"
      >
        <div class="w-[284px] shrink-0">{{ __('Name') }}</div>
        <div class="min-w-0 flex-1">{{ __('Subject') }}</div>
        <div class="w-[152px] shrink-0">{{ __('Used in') }}</div>
        <div class="w-[135px] shrink-0">{{ __('Active') }}</div>
      </div>
      <ul
        class="overflow-y-auto rounded-b-lg border border-t-0 border-[var(--ct-border)]"
      >
        <template v-for="(template, i) in templatesList" :key="template.name">
          <li
            class="flex cursor-pointer items-center gap-4 px-4 py-2.5 hover:bg-surface-gray-2"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div
              class="w-[284px] shrink-0 truncate text-[14px] font-medium leading-5 text-ink-gray-9"
            >
              {{ template.name }}
            </div>
            <div
              class="min-w-0 flex-1 truncate text-[14px] leading-5 text-ink-gray-6"
            >
              {{ template.subject }}
            </div>
            <div
              class="w-[152px] shrink-0 text-[14px] leading-5 text-ink-gray-6"
            >
              {{ usedIn(template.reference_doctype) }}
            </div>
            <!-- the menu (duplicate, delete) is not in the Figma: kept at the end -->
            <div
              class="flex h-5 w-[135px] shrink-0 items-center justify-between"
            >
              <Switch
                v-model="template.enabled"
                size="md"
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
            class="h-px bg-[var(--ct-border)]"
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
import LucideFileText from '~icons/lucide/file-text'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsSectionTabs from '@/components/Settings/SettingsSectionTabs.vue'
import { emailTabs } from '@/components/Settings/emailConfig'
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

// "Usado em": deal templates are used on the cards, lead ones on the contacts
function usedIn(doctype) {
  return doctype === 'CRM Deal' ? __('Cards') : __('Contacts')
}

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
