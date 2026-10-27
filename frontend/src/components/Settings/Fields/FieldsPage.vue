<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex w-9/12 flex-col gap-1">
        <h2 class="flex h-5 text-2xl-semibold leading-none">
          {{ __('Fields') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Fields of the company, shared by every funnel. Each funnel chooses which ones it uses and in which stages.',
            )
          }}
        </p>
      </div>
      <div class="flex w-3/12 flex-col items-end gap-1">
        <Button
          :label="__('New field')"
          icon-left="lucide-plus"
          variant="solid"
          :disabled="limitReached"
          @click="openNew"
        />
        <span class="text-xs text-ink-gray-5" data-testid="field-usage">
          {{ __('{0} of {1} custom fields', [catalog.used, catalog.limit]) }}
        </span>
        <span
          v-if="textRoomIsTighter"
          class="text-xs text-ink-gray-5"
          data-testid="field-text-room"
        >
          {{ __('Room for {0} more text, list or link fields', [textRoom]) }}
        </span>
      </div>
    </div>

    <div
      v-if="loading && !catalog.fields.length"
      class="mt-12 flex items-center justify-center"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="w-full overflow-y-auto">
      <div class="flex items-center p-2 text-sm text-ink-gray-5">
        <div class="w-5/12">{{ __('Field') }}</div>
        <div class="w-3/12">{{ __('Type') }}</div>
        <div class="w-2/12">{{ __('Origin') }}</div>
        <div class="w-2/12" />
      </div>
      <div class="mx-2 h-px border-t border-outline-elevation-2" />
      <template v-for="(field, i) in catalog.fields" :key="field.fieldname">
        <div
          class="flex items-center rounded-4 p-3"
          :class="field.disabled && 'opacity-50'"
          :data-field="field.fieldname"
        >
          <div class="w-5/12 truncate text-base-medium text-ink-gray-7">
            {{ __(field.label) }}
            <span v-if="field.disabled" class="ml-1 text-sm text-ink-gray-5">
              ({{ __('disabled') }})
            </span>
          </div>
          <div class="w-3/12 text-base text-ink-gray-6">
            {{ fieldTypeLabel(field) }}
          </div>
          <div class="w-2/12 text-base text-ink-gray-6">
            {{ field.is_standard ? __('Standard') : __('Created') }}
          </div>
          <div class="flex w-2/12 justify-end">
            <Dropdown
              v-if="!field.is_standard && !field.disabled"
              :options="actions(field)"
              align="end"
              @update:open="(open) => open && (confirmingDisable = null)"
            >
              <Button icon="lucide-more-horizontal" variant="ghost" />
            </Dropdown>
          </div>
        </div>
        <hr v-if="catalog.fields.length !== i + 1" class="mx-2" />
      </template>
    </div>
  </div>

  <Dialog
    v-model:open="dialog.show"
    :title="dialog.fieldname ? __('Edit field') : __('New field')"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <FormControl v-model="dialog.label" :label="__('Name')" />
        <FormControl
          type="select"
          :label="__('Type')"
          :options="typeOptions"
          :disabled="Boolean(dialog.fieldname)"
          :model-value="dialog.fieldtype"
          @update:model-value="(v) => (dialog.fieldtype = v)"
        />
        <FormControl
          v-if="dialog.fieldtype === 'Select'"
          v-model="dialog.options"
          type="textarea"
          :label="__('Options (one per line)')"
        />
        <FormControl
          v-if="dialog.fieldtype === 'Link'"
          type="select"
          :label="__('Links to')"
          :options="linkOptions"
          :disabled="Boolean(dialog.fieldname)"
          :model-value="dialog.options"
          @update:model-value="(v) => (dialog.options = v)"
        />
        <ErrorMessage
          v-if="!dialog.fieldname && noRoomForType"
          :message="noRoomForType"
        />
        <ErrorMessage :message="dialog.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="dialog.show = false" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="dialog.saving"
          :disabled="!dialog.fieldname && Boolean(noRoomForType)"
          @click="saveField"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { pipelinesStore } from '@/stores/pipelines'
import { fieldTypeLabel, fieldTypeOptions } from './fieldTypes'
import { ConfirmDelete } from '@/utils'
import {
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref } from 'vue'

const pipelineStore = pipelinesStore()

const loading = ref(false)
const catalog = ref({ limit: 60, used: 0, fields: [] })
// The cards table also has a size limit per row: text, list and link fields
// run out of room before the field limit (see fields.py, room_by_type)
const room = computed(() => catalog.value.room || null)
const textRoom = computed(() => room.value?.Data ?? null)
const textRoomIsTighter = computed(
  () =>
    textRoom.value !== null &&
    textRoom.value < catalog.value.limit - catalog.value.used,
)
const limitReached = computed(
  () =>
    catalog.value.used >= catalog.value.limit ||
    (room.value && Object.values(room.value).every((n) => n <= 0)),
)
const noRoomForType = computed(() => {
  if (!room.value || room.value[dialog.fieldtype] !== 0) return ''
  return ['Data', 'Select', 'Link'].includes(dialog.fieldtype)
    ? __(
        'There is no room left for another text, list or link field in cards. Number, date and Yes/No fields take much less space and can still be created.',
      )
    : __('There is no room left for another field of this type in cards.')
})

const typeOptions = fieldTypeOptions()
const linkOptions = [
  { label: __('Contact'), value: 'Contact' },
  { label: __('Organization'), value: 'CRM Organization' },
]

const dialog = reactive({
  show: false,
  fieldname: null,
  label: '',
  fieldtype: 'Data',
  options: '',
  error: '',
  saving: false,
})

function openNew() {
  Object.assign(dialog, {
    show: true,
    fieldname: null,
    label: '',
    fieldtype: 'Data',
    options: '',
    error: '',
  })
}

function openEdit(field) {
  Object.assign(dialog, {
    show: true,
    fieldname: field.fieldname,
    label: field.label,
    fieldtype: field.fieldtype,
    options: field.options || '',
    error: '',
  })
}

function validate() {
  if (!dialog.label.trim()) return __('Give the field a name.')
  if (dialog.fieldtype === 'Select' && !dialog.options.trim()) {
    return __('Write at least one option.')
  }
  if (dialog.fieldtype === 'Link' && !dialog.options) {
    return __('Choose what the field links to.')
  }
  return ''
}

async function saveField() {
  dialog.error = validate()
  if (dialog.error) return
  dialog.saving = true
  let options = ['Select', 'Link'].includes(dialog.fieldtype)
    ? dialog.options
    : null
  try {
    if (dialog.fieldname) {
      await pipelineStore.apiCall('update_field', {
        fieldname: dialog.fieldname,
        label: dialog.label.trim(),
        options: dialog.fieldtype === 'Select' ? options : null,
      })
    } else {
      await pipelineStore.apiCall('create_field', {
        label: dialog.label.trim(),
        fieldtype: dialog.fieldtype,
        options,
      })
    }
    dialog.show = false
    toast.success(__('Field saved'))
    await load()
  } catch (e) {
    dialog.error = e?.messages?.join('\n') || __('Could not save the field')
  } finally {
    dialog.saving = false
  }
}

async function disable(field) {
  try {
    await pipelineStore.apiCall('disable_field', { fieldname: field.fieldname })
    toast.success(__('Field disabled. Its values stay saved.'))
    await load()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not disable the field'))
  }
}

// Disabling cannot be undone from here, so it takes a second click (one
// confirm state per row, reset whenever a row's menu opens)
const confirmingDisable = ref(null)

function actions(field) {
  let isConfirming = {
    get value() {
      return confirmingDisable.value === field.fieldname
    },
    set value(v) {
      confirmingDisable.value = v ? field.fieldname : null
    },
  }
  return [
    {
      label: __('Edit'),
      icon: 'lucide-pencil',
      onClick: () => openEdit(field),
    },
    ...ConfirmDelete({
      isConfirmingDelete: isConfirming,
      onConfirmDelete: () => disable(field),
      label: __('Disable'),
    }),
  ]
}

async function load() {
  loading.value = true
  try {
    catalog.value =
      (await pipelineStore.apiCall('get_field_catalog')) || catalog.value
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the fields'))
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
