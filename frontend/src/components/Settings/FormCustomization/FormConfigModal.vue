<template>
  <Dialog v-model:open="show" :size="'3xl'" :title="__('Configure form')">
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">
          {{ isCards ? `${pipelineLabel} · ${stageLabel}` : formLabel }}
        </p>
        <p class="text-p-sm text-ink-gray-5">
          {{
            !isCards
              ? __(
                  'Drag to change the order. Hidden fields keep what was filled in; required fields are asked when someone creates the record.',
                )
              : stage
                ? __(
                    'Visible, required and read only apply to this stage. The order belongs to the funnel: change it in All stages of the funnel.',
                  )
                : __(
                    'Drag to change the order. What you set here applies to every stage of the funnel.',
                  )
          }}
        </p>
        <div
          class="flex items-center gap-2 px-2 text-sm text-ink-gray-5"
          aria-hidden="true"
        >
          <span class="w-4" />
          <span class="flex-1">{{ __('Field') }}</span>
          <span class="w-20 text-center">{{ __('Visible') }}</span>
          <span class="w-20 text-center">{{ __('Required') }}</span>
          <span v-if="isCards" class="w-20 text-center">{{
            __('Read only')
          }}</span>
          <span class="w-7" />
        </div>
        <Draggable
          :list="rows"
          item-key="fieldname"
          handle=".row-handle"
          :disabled="Boolean(stage)"
          class="flex max-h-[55vh] flex-col overflow-y-auto rounded border border-outline-gray-2"
        >
          <template #item="{ element: row, index }">
            <div
              class="flex items-center gap-2 border-b border-outline-gray-1 px-2 py-2 last:border-b-0"
              :data-field="row.fieldname"
            >
              <span
                v-if="row.locked"
                class="lucide-lock size-4 shrink-0 text-ink-gray-4"
                :aria-label="__('Always shown')"
              />
              <span
                v-else
                class="row-handle lucide-grip-vertical size-4 shrink-0 text-ink-gray-4"
                :class="stage ? 'opacity-40' : 'cursor-grab'"
              />
              <div class="flex min-w-0 flex-1 flex-col">
                <span class="truncate text-base text-ink-gray-8">
                  {{ __(row.label) }}
                </span>
                <span v-if="row.locked" class="text-xs text-ink-gray-5">
                  {{ __('Always shown') }}
                </span>
                <span
                  v-else-if="varyingFlags(row).length"
                  class="text-xs text-ink-amber-6"
                >
                  {{
                    __('Varies by stage: {0}', [varyingFlags(row).join(', ')])
                  }}
                </span>
              </div>
              <template v-if="row.locked">
                <span
                  class="shrink-0"
                  :class="isCards ? 'w-64' : 'w-[10.5rem]'"
                />
              </template>
              <template v-else>
                <div class="flex w-20 justify-center">
                  <Switch
                    size="sm"
                    :aria-label="__('Visible')"
                    :model-value="Boolean(row.visible)"
                    :disabled="!canManage"
                    @update:model-value="(v) => setFlag(row, 'visible', v)"
                  />
                </div>
                <div class="flex w-20 justify-center">
                  <Checkbox
                    :aria-label="__('Required')"
                    :model-value="Boolean(row.required)"
                    :disabled="!canManage || !row.can_require"
                    @update:model-value="(v) => setFlag(row, 'required', v)"
                  />
                </div>
                <div v-if="isCards" class="flex w-20 justify-center">
                  <Checkbox
                    :aria-label="__('Read only')"
                    :model-value="Boolean(row.read_only)"
                    :disabled="!canManage"
                    @update:model-value="(v) => setFlag(row, 'read_only', v)"
                  />
                </div>
              </template>
              <div class="w-7">
                <Button
                  v-if="isCards && !row.locked && !stage && canManage"
                  variant="ghost"
                  icon="lucide-x"
                  :tooltip="__('Remove from this funnel')"
                  :aria-label="__('Remove from this funnel')"
                  @click="rows.splice(index, 1)"
                />
              </div>
            </div>
          </template>
        </Draggable>
        <div
          v-if="isCards && !stage && canManage && freeFields.length"
          class="w-72"
        >
          <FormControl
            type="select"
            :placeholder="__('Use another field')"
            :options="freeFields"
            :model-value="null"
            @update:model-value="addField"
          />
        </div>
        <div
          v-if="confirming"
          class="rounded bg-surface-amber-1 p-3 text-p-sm text-ink-amber-7"
          data-testid="equalize-warning"
        >
          {{
            __(
              'These fields are different in each stage today and will be the same in every stage: {0}.',
              [confirming.map((r) => __(r.label)).join(', ')],
            )
          }}
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          v-if="canManage"
          variant="solid"
          :label="confirming ? __('Confirm and save') : __('Save')"
          :loading="saving"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  configPayload,
  configRows,
  equalizedRows,
  newRow,
  setFlag,
  unusedFields,
} from '@/utils/formConfig'
import Draggable from 'vuedraggable'
import {
  Checkbox,
  Dialog,
  ErrorMessage,
  FormControl,
  Switch,
  call,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const show = defineModel({ type: Boolean, default: false })

const props = defineProps({
  pipeline: { type: String, required: true },
  // CRM Deal (per funnel and stage), CRM Organization or Contact (one form)
  doctype: { type: String, default: 'CRM Deal' },
  formLabel: { type: String, default: '' },
  pipelineLabel: { type: String, default: '' },
  // '' = all stages of the funnel (batch edit)
  stage: { type: String, default: '' },
  stageLabel: { type: String, default: '' },
  // crm.api.forms.get_form_schema().fields
  fields: { type: Array, default: () => [] },
  // crm.api.pipeline.get_field_catalog().fields
  catalog: { type: Array, default: () => [] },
  canManage: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])

const isCards = computed(() => props.doctype === 'CRM Deal')

const rows = ref([])
const saving = ref(false)
const error = ref('')
const confirming = ref(null)

watch(
  show,
  (open) => {
    if (!open) return
    rows.value = configRows(props.fields)
    error.value = ''
    confirming.value = null
  },
  { immediate: true },
)

const flagLabels = {
  visible: __('Visible'),
  required: __('Required'),
  read_only: __('Read only'),
}

function varyingFlags(row) {
  return Object.keys(flagLabels)
    .filter((flag) => row[flag] === null)
    .map((flag) => flagLabels[flag].toLowerCase())
}

const freeFields = computed(() =>
  unusedFields(props.catalog, rows.value).map((f) => ({
    label: __(f.label),
    value: f.fieldname,
  })),
)

function addField(fieldname) {
  let field = props.catalog.find((f) => f.fieldname === fieldname)
  if (field) rows.value.push(newRow(field))
}

async function save() {
  error.value = ''
  // fields that differ between stages become equal: say it before saving
  let equalized = props.stage || !isCards.value ? [] : equalizedRows(rows.value)
  if (equalized.length && !confirming.value) {
    confirming.value = equalized
    return
  }
  saving.value = true
  try {
    let schema = await call('crm.api.forms.save_form_config', {
      doctype: props.doctype,
      pipeline: props.pipeline || null,
      stage: props.stage || null,
      fields: configPayload(rows.value),
    })
    emit('saved', schema)
    show.value = false
  } catch (e) {
    error.value = e?.messages?.join('\n') || __('Could not save the form')
  } finally {
    saving.value = false
  }
}
</script>
