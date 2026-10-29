<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex w-8/12 flex-col gap-1">
        <h2 class="flex h-5 text-2xl-semibold leading-none">
          {{ __('Form customization') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Which fields each form shows, in which order and which are required. Hiding a field never deletes what was filled in.',
            )
          }}
        </p>
      </div>
      <div v-if="isManager()" class="flex w-4/12 flex-col items-end gap-1">
        <div class="flex gap-2">
          <Button
            :label="__('Created fields')"
            data-testid="created-fields"
            @click="showCreated = true"
          />
          <Button
            :label="__('Add field')"
            icon-left="lucide-plus"
            variant="solid"
            :disabled="limitReached"
            @click="openField(null)"
          />
        </div>
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

    <div class="px-2">
      <TabButtons v-model="tab" :options="tabs" />
    </div>

    <div class="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-2">
      <div
        v-if="isCards && !pipelines.length && !loading"
        class="text-p-base text-ink-gray-5"
      >
        {{ __('You do not take part in any funnel yet.') }}
      </div>
      <template v-else>
        <div class="flex flex-wrap items-end gap-3">
          <p v-if="!isCards" class="flex-1 text-p-sm text-ink-gray-5">
            {{
              isCompanies
                ? __(
                    'One form for every organization of the company, including the Receita Federal data the CNPJ lookup fills in.',
                  )
                : __('One form for every contact of the company.')
            }}
          </p>
          <div v-if="isCards" class="w-56">
            <FormControl
              type="select"
              :label="__('Funnel')"
              :options="pipelineOptions"
              :model-value="pipeline"
              @update:model-value="(v) => (pipeline = v)"
            />
          </div>
          <div v-if="isCards" class="w-64">
            <FormControl
              type="select"
              :label="__('Stage')"
              :options="stageOptions"
              :model-value="stage"
              @update:model-value="(v) => (stage = v)"
            />
          </div>
          <div v-if="isCards" class="w-56" data-testid="form-block">
            <FormControl
              type="select"
              :label="__('Fields of')"
              :options="blockOptions"
              :model-value="block"
              @update:model-value="(v) => (block = v)"
            />
          </div>
          <div class="flex flex-1 items-center justify-end gap-2">
            <Badge
              v-if="(pipeline || !isCards) && !canManage"
              :label="__('Read only')"
              variant="subtle"
            />
            <Button
              v-if="canManage"
              :label="__('Configure form')"
              icon-left="lucide-settings-2"
              variant="solid"
              :disabled="!schema"
              @click="showConfig = true"
            />
          </div>
        </div>

        <div class="rounded-lg border border-outline-gray-2 p-4">
          <div class="mb-3 flex items-center justify-between">
            <span class="text-base-medium text-ink-gray-8">
              {{ __('Form preview') }}
            </span>
            <span class="text-sm text-ink-gray-5">
              {{ previewHint }}
            </span>
          </div>
          <div v-if="loadingSchema" class="flex justify-center py-6">
            <LoadingIndicator class="w-4" />
          </div>
          <ErrorMessage v-else-if="schemaError" :message="schemaError" />
          <p
            v-else-if="isBlock && !schema?.fields?.length"
            class="text-p-base text-ink-gray-5"
          >
            {{
              __(
                'No field of the {0} on the card yet. Use Configure form to choose them.',
                [blockLabel],
              )
            }}
          </p>
          <FormPreview
            v-else
            :fields="schema?.fields || []"
            :in-funnel="isCards"
          />
        </div>
      </template>
    </div>
  </div>

  <FormConfigModal
    v-if="schema"
    v-model="showConfig"
    :doctype="doctype"
    :form-label="formLabel"
    :pipeline="isCards ? pipeline : ''"
    :pipeline-label="currentPipeline ? __(currentPipeline.pipeline_name) : ''"
    :stage="isCards ? stage : ''"
    :stage-label="stageLabel"
    :block="isCards ? block : 'Card'"
    :block-label="blockLabel"
    :fields="schema.fields"
    :catalog="isBlock ? blockCatalog.fields : catalog.fields"
    :can-manage="canManage"
    @saved="onConfigSaved"
  />

  <FieldDialog
    v-model="showField"
    :doctype="doctype"
    :field="editing"
    :pipelines="isCards ? manageablePipelines : []"
    :pipeline="pipeline"
    :stage="stage"
    :room="catalog.room"
    @saved="onFieldSaved"
  />

  <Dialog v-model:open="showCreated" :title="__('Created fields')">
    <template #default>
      <div v-if="!createdFields.length" class="text-p-base text-ink-gray-5">
        {{ __('No field was created yet.') }}
      </div>
      <div v-else class="flex flex-col">
        <div
          v-for="field in createdFields"
          :key="field.fieldname"
          class="flex items-center gap-3 border-b border-outline-gray-1 py-2 last:border-b-0"
          :class="field.disabled && 'opacity-50'"
          :data-field="field.fieldname"
        >
          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
            {{ __(field.label) }}
            <span v-if="field.disabled" class="ml-1 text-sm text-ink-gray-5">
              ({{ __('disabled') }})
            </span>
          </span>
          <span class="w-36 truncate text-sm text-ink-gray-6">
            {{ fieldTypeLabel(field) }}
          </span>
          <div class="w-8">
            <Dropdown
              :options="fieldActions(field)"
              align="end"
              @update:open="(open) => open && (confirmingDisable = null)"
            >
              <Button icon="lucide-more-horizontal" variant="ghost" />
            </Dropdown>
          </div>
        </div>
      </div>
    </template>
  </Dialog>

  <Dialog
    :open="Boolean(deleting)"
    :title="__('Delete field')"
    @update:open="(open) => !open && (deleting = null)"
  >
    <template #default>
      <div
        v-if="deleting"
        class="flex flex-col gap-3 text-p-base text-ink-gray-8"
      >
        <p>
          {{
            __(
              'Delete the field {0}? It leaves every form, funnel rule and list.',
              [__(deleting.field.label)],
            )
          }}
        </p>
        <p v-if="deleting.records" class="font-medium text-ink-red-4">
          {{
            __(
              '{0} records have a value in this field. The values will be deleted and this cannot be undone.',
              [deleting.records],
            )
          }}
        </p>
        <p v-else class="text-ink-gray-6">
          {{ __('No record has a value in this field.') }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="deleting = null" />
        <Button
          :label="__('Delete')"
          theme="red"
          variant="solid"
          :loading="deleteLoading"
          @click="confirmDelete"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FormPreview from './FormPreview.vue'
import FormConfigModal from './FormConfigModal.vue'
import FieldDialog from './FieldDialog.vue'
import { fieldTypeLabel } from '../Fields/fieldTypes'
import { pipelinesStore } from '@/stores/pipelines'
import { usersStore } from '@/stores/users'
import { ConfirmDelete } from '@/utils'
import {
  Badge,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  TabButtons,
  call,
  toast,
} from 'frappe-ui'
import { computed, onMounted, ref, watch } from 'vue'

const pipelineStore = pipelinesStore()
// admins on the server (crm.permissions.pipeline.is_admin) include Sales
// Managers outside the sales hierarchy; the server still checks every change
const { isManager } = usersStore()

// one tab per form: cards (per funnel and stage), organizations and contacts
// (one form each for the whole company)
const FORMS = {
  cards: 'CRM Deal',
  organizations: 'CRM Organization',
  contacts: 'Contact',
}
const tab = ref('cards')
const tabs = [
  { label: __('Cards'), value: 'cards' },
  { label: __('Organizations'), value: 'organizations' },
  { label: __('Contacts'), value: 'contacts' },
]
const doctype = computed(() => FORMS[tab.value])
const isCards = computed(() => tab.value === 'cards')
const isCompanies = computed(() => tab.value === 'organizations')
const formLabel = computed(
  () => tabs.find((t) => t.value === tab.value)?.label || '',
)
const previewHint = computed(() =>
  isCards.value
    ? __('As the salesperson sees the card')
    : isCompanies.value
      ? __('As the team sees an organization')
      : __('As the team sees a contact'),
)

const loading = ref(true)
// cards: the card's own fields or those of its organization, second
// organization or primary contact that the stage shows (credtech#196)
const block = ref('Card')
const isBlock = computed(() => isCards.value && block.value !== 'Card')
const blockCatalog = ref({ fields: [] })
const blockOptions = computed(() =>
  (
    schema.value?.blocks || [
      { block: 'Card', label: __('Card') },
      { block: 'Organization', label: __('Organization') },
      { block: 'Second organization', label: __('Second organization') },
      { block: 'Contact', label: __('Contact') },
    ]
  ).map((b) => ({ label: b.label, value: b.block })),
)
const blockLabel = computed(
  () => blockOptions.value.find((o) => o.value === block.value)?.label || '',
)
const pipeline = ref('')
// '' = all stages of the funnel
const stage = ref('')
const schema = ref(null)
const loadingSchema = ref(false)
const schemaError = ref('')
const catalog = ref({ limit: 60, used: 0, room: null, fields: [] })

const showConfig = ref(false)
const showField = ref(false)
const showCreated = ref(false)
const editing = ref(null)

const pipelines = computed(() => pipelineStore.pipelines)
const currentPipeline = computed(() =>
  pipelineStore.getPipeline(pipeline.value),
)
// cards: funnel owners; organizations and contacts: admins (managers)
const canManage = computed(() =>
  isCards.value
    ? ['Admin', 'Owner'].includes(currentPipeline.value?.my_role)
    : isManager(),
)
const manageablePipelines = computed(() =>
  pipelines.value.filter((p) => ['Admin', 'Owner'].includes(p.my_role)),
)

const pipelineOptions = computed(() =>
  pipelines.value.map((p) => ({ label: __(p.pipeline_name), value: p.name })),
)
const stageOptions = computed(() => [
  { label: __('All stages of the funnel'), value: '' },
  ...(currentPipeline.value?.stages || []).map((s) => ({
    label: __(s.deal_status),
    value: s.name,
  })),
])
const stageLabel = computed(
  () => stageOptions.value.find((o) => o.value === stage.value)?.label || '',
)

// The cards table also has a size limit per row: text, list and link fields
// run out of room before the field limit (see fields.py, room_by_type)
const textRoom = computed(() => catalog.value.room?.Data ?? null)
const textRoomIsTighter = computed(
  () =>
    textRoom.value !== null &&
    textRoom.value < catalog.value.limit - catalog.value.used,
)
const limitReached = computed(
  () =>
    catalog.value.used >= catalog.value.limit ||
    (catalog.value.room &&
      Object.values(catalog.value.room).every((n) => n <= 0)),
)
const createdFields = computed(() =>
  catalog.value.fields.filter((f) => !f.is_standard),
)

let schemaRequest = 0
async function loadSchema() {
  let request = ++schemaRequest
  if (isCards.value && !pipeline.value) {
    schema.value = null
    return
  }
  loadingSchema.value = true
  schemaError.value = ''
  try {
    let result = await call(
      'crm.api.forms.get_form_schema',
      isCards.value
        ? {
            doctype: doctype.value,
            pipeline: pipeline.value,
            stage: stage.value || null,
            block: block.value,
          }
        : { doctype: doctype.value },
    )
    if (request === schemaRequest) schema.value = result
  } catch (e) {
    if (request !== schemaRequest) return
    schema.value = null
    schemaError.value = e?.messages?.[0] || __('Could not load the form')
  } finally {
    if (request === schemaRequest) loadingSchema.value = false
  }
}

watch(pipeline, () => {
  stage.value = ''
  loadSchema()
})
watch(stage, loadSchema)
watch(block, () => {
  loadSchema()
  loadBlockCatalog()
})

const BLOCK_DOCTYPES = {
  Organization: 'CRM Organization',
  'Second organization': 'CRM Organization',
  Contact: 'Contact',
}

async function loadBlockCatalog() {
  if (!isBlock.value) return
  try {
    blockCatalog.value = (await call('crm.api.forms.get_fields', {
      doctype: BLOCK_DOCTYPES[block.value],
    })) || { fields: [] }
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the fields'))
  }
}
watch(tab, () => {
  schema.value = null
  block.value = 'Card'
  Promise.all([loadCatalog(), loadSchema()])
})

async function loadCatalog() {
  try {
    catalog.value =
      (await call('crm.api.forms.get_fields', { doctype: doctype.value })) ||
      catalog.value
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the fields'))
  }
}

// cards on screen read the funnel's config and catalog from the store cache
async function refresh() {
  await pipelineStore.reload()
  await Promise.all([loadCatalog(), loadSchema()])
}

function onConfigSaved(saved) {
  schema.value = saved
  toast.success(__('Form saved'))
  pipelineStore.reload()
}

function onFieldSaved() {
  editing.value = null
  refresh()
}

function openField(field) {
  editing.value = field
  showField.value = true
}

async function disable(field) {
  try {
    await call('crm.api.forms.disable_field', {
      fieldname: field.fieldname,
      doctype: doctype.value,
    })
    toast.success(__('Field disabled. Its values stay saved.'))
    await refresh()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not disable the field'))
  }
}

// Disabling cannot be undone from here, so it takes a second click (one
// confirm state per row, reset whenever a row's menu opens)
const confirmingDisable = ref(null)

const deleting = ref(null)
const deleteLoading = ref(false)

// Deleting removes the column and its values (credtech#232): the dialog says how many records have a value first
async function askDelete(field) {
  try {
    let usage = await call('crm.api.forms.field_usage', {
      fieldname: field.fieldname,
      doctype: doctype.value,
    })
    deleting.value = { field, records: usage.records }
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not delete the field'))
  }
}

async function confirmDelete() {
  deleteLoading.value = true
  try {
    await call('crm.api.forms.delete_field', {
      fieldname: deleting.value.field.fieldname,
      doctype: doctype.value,
    })
    toast.success(__('Field deleted'))
    deleting.value = null
    await refresh()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not delete the field'))
  } finally {
    deleteLoading.value = false
  }
}

async function enable(field) {
  try {
    await call('crm.api.forms.enable_field', {
      fieldname: field.fieldname,
      doctype: doctype.value,
    })
    toast.success(__('Field enabled'))
    await refresh()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not enable the field'))
  }
}

function fieldActions(field) {
  let remove = {
    label: __('Delete'),
    icon: 'lucide-trash-2',
    onClick: () => {
      showCreated.value = false
      askDelete(field)
    },
  }
  if (field.disabled) {
    return [
      { label: __('Enable'), icon: 'lucide-eye', onClick: () => enable(field) },
      remove,
    ]
  }
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
      onClick: () => {
        showCreated.value = false
        openField(field)
      },
    },
    ...ConfirmDelete({
      isConfirmingDelete: isConfirming,
      onConfirmDelete: () => disable(field),
      label: __('Disable'),
      icon: 'lucide-eye-off',
    }),
    remove,
  ]
}

onMounted(async () => {
  try {
    await Promise.all([pipelineStore.ensureLoaded(), loadCatalog()])
    pipeline.value = pipelines.value[0]?.name || ''
  } finally {
    loading.value = false
  }
})
</script>
