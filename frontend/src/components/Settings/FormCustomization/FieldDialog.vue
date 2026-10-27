<template>
  <Dialog
    v-model:open="show"
    :title="field ? __('Edit field') : __('New field')"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <FormControl v-model="form.label" :label="__('Name')" />
        <FormControl
          type="select"
          :label="__('Type')"
          :options="typeOptions"
          :disabled="Boolean(field)"
          :model-value="form.fieldtype"
          @update:model-value="(v) => (form.fieldtype = v)"
        />
        <FormControl
          v-if="form.fieldtype === 'Select'"
          v-model="form.options"
          type="textarea"
          :label="__('Options (one per line)')"
        />
        <FormControl
          v-if="form.fieldtype === 'Link'"
          type="select"
          :label="__('Links to')"
          :options="linkOptions"
          :disabled="Boolean(field)"
          :model-value="form.options"
          @update:model-value="(v) => (form.options = v)"
        />

        <!-- where a new card field shows up (credtech#180) -->
        <div v-if="!field && pipelines.length" class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">
            {{ __('Funnels where it shows up') }}
          </span>
          <div
            v-for="p in pipelines"
            :key="p.name"
            class="flex flex-col gap-1.5"
            :data-pipeline="p.name"
          >
            <label class="flex items-center gap-2 text-base text-ink-gray-8">
              <Checkbox
                :model-value="Boolean(places[p.name])"
                @update:model-value="(v) => togglePipeline(p, v)"
              />
              {{ __(p.pipeline_name) }}
            </label>
            <div
              v-if="places[p.name]"
              class="ml-6 flex flex-col gap-1.5 text-sm text-ink-gray-7"
            >
              <label class="flex items-center gap-2">
                <input
                  v-model="places[p.name].all"
                  type="radio"
                  :value="true"
                  :name="`stages-${p.name}`"
                />
                {{ __('All stages') }}
              </label>
              <label class="flex items-center gap-2">
                <input
                  v-model="places[p.name].all"
                  type="radio"
                  :value="false"
                  :name="`stages-${p.name}`"
                />
                {{ __('Only these stages:') }}
              </label>
              <div
                v-if="!places[p.name].all"
                class="ml-6 flex flex-wrap gap-x-4 gap-y-1"
              >
                <label
                  v-for="s in p.stages"
                  :key="s.name"
                  class="flex items-center gap-1.5"
                >
                  <Checkbox
                    :model-value="places[p.name].stages.includes(s.name)"
                    @update:model-value="(v) => toggleStage(p.name, s.name, v)"
                  />
                  {{ __(s.deal_status) }}
                </label>
              </div>
            </div>
          </div>
          <label
            v-if="Object.keys(places).length"
            class="flex items-center gap-2 text-base text-ink-gray-8"
          >
            <Checkbox v-model="form.required" />
            {{ __('Required in these stages') }}
          </label>
          <span
            v-if="!Object.keys(places).length"
            class="text-p-sm text-ink-gray-5"
          >
            {{
              __(
                'Without a funnel the field is created but no card shows it until a funnel uses it.',
              )
            }}
          </span>
        </div>

        <ErrorMessage v-if="!field && noRoomForType" :message="noRoomForType" />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="field ? __('Save') : __('Create')"
          :loading="saving"
          :disabled="!field && Boolean(noRoomForType)"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { fieldTypeOptions } from '../Fields/fieldTypes'
import {
  Checkbox,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const show = defineModel({ type: Boolean, default: false })

const props = defineProps({
  // a created field to edit; null = new field
  field: { type: Object, default: null },
  // funnels the new field can go to (the user manages them), with stages
  pipelines: { type: Array, default: () => [] },
  // funnel and stage chosen on the page: the new field starts there
  pipeline: { type: String, default: '' },
  stage: { type: String, default: '' },
  // crm.api.pipeline.get_field_catalog().room
  room: { type: Object, default: null },
})

const emit = defineEmits(['saved'])

const typeOptions = fieldTypeOptions()
const linkOptions = [
  { label: __('Contact'), value: 'Contact' },
  { label: __('Organization'), value: 'CRM Organization' },
]

const form = reactive({
  label: '',
  fieldtype: 'Data',
  options: '',
  required: false,
})
// { [pipeline]: { all: bool, stages: [stage keys] } }
const places = reactive({})
const saving = ref(false)
const error = ref('')

watch(
  show,
  (open) => {
    if (!open) return
    Object.assign(form, {
      label: props.field?.label || '',
      fieldtype: props.field?.fieldtype || 'Data',
      options: props.field?.options || '',
      required: false,
    })
    for (let key of Object.keys(places)) delete places[key]
    if (
      !props.field &&
      props.pipelines.some((p) => p.name === props.pipeline)
    ) {
      places[props.pipeline] = props.stage
        ? { all: false, stages: [props.stage] }
        : { all: true, stages: [] }
    }
    error.value = ''
  },
  { immediate: true },
)

const noRoomForType = computed(() => {
  if (!props.room || props.room[form.fieldtype] !== 0) return ''
  return ['Data', 'Select', 'Link'].includes(form.fieldtype)
    ? __(
        'There is no room left for another text, list or link field in cards. Number, date and Yes/No fields take much less space and can still be created.',
      )
    : __('There is no room left for another field of this type in cards.')
})

function togglePipeline(pipeline, checked) {
  if (checked) places[pipeline.name] = { all: true, stages: [] }
  else delete places[pipeline.name]
}

function toggleStage(pipeline, stage, checked) {
  let stages = places[pipeline].stages
  if (checked && !stages.includes(stage)) stages.push(stage)
  if (!checked) stages.splice(stages.indexOf(stage), 1)
}

function validate() {
  if (!form.label.trim()) return __('Give the field a name.')
  if (form.fieldtype === 'Select' && !form.options.trim()) {
    return __('Write at least one option.')
  }
  if (form.fieldtype === 'Link' && !form.options) {
    return __('Choose what the field links to.')
  }
  let empty = Object.entries(places).find(([, p]) => !p.all && !p.stages.length)
  if (empty) return __('Choose at least one stage in each funnel.')
  return ''
}

async function save() {
  error.value = validate()
  if (error.value) return
  saving.value = true
  let options = ['Select', 'Link'].includes(form.fieldtype)
    ? form.options
    : null
  try {
    let saved
    if (props.field) {
      saved = await call('crm.api.forms.update_field', {
        fieldname: props.field.fieldname,
        label: form.label.trim(),
        options: form.fieldtype === 'Select' ? options : null,
      })
    } else {
      saved = await call('crm.api.forms.create_field', {
        label: form.label.trim(),
        fieldtype: form.fieldtype,
        options,
        placement: Object.entries(places).map(([pipeline, p]) => ({
          pipeline,
          stages: p.all ? [] : p.stages,
        })),
        required: form.required ? 1 : 0,
      })
    }
    toast.success(__('Field saved'))
    emit('saved', saved)
    show.value = false
  } catch (e) {
    error.value = e?.messages?.join('\n') || __('Could not save the field')
  } finally {
    saving.value = false
  }
}
</script>
