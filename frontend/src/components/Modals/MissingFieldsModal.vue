<template>
  <Dialog
    v-model:open="show"
    :title="__('Fill in to move the card')"
    @close="cancel"
  >
    <template #default>
      <div class="-mt-3 mb-4 text-p-base text-ink-gray-7">
        {{ __('The stage {0} requires these fields.', [stageLabel]) }}
      </div>
      <div class="flex flex-col gap-3">
        <div v-for="field in fields" :key="field.fieldname">
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __(field.label) }}
            <span class="text-ink-red-4">*</span>
          </div>
          <Link
            v-if="field.fieldtype === 'Link'"
            class="form-control flex-1 truncate"
            :value="values[field.fieldname]"
            :doctype="field.options"
            @change="(v) => (values[field.fieldname] = v)"
          />
          <DatePicker
            v-else-if="field.fieldtype === 'Date'"
            :model-value="values[field.fieldname]"
            variant="outline"
            :format="getFormat('', '', true, false, false)"
            @change="(v) => (values[field.fieldname] = v)"
          />
          <AttachControl
            v-else-if="field.fieldtype === 'Attach'"
            :value="values[field.fieldname]"
            doctype="CRM Deal"
            :docname="deal"
            :fieldname="field.fieldname"
            @change="(v) => (values[field.fieldname] = v)"
          />
          <FormControl
            v-else-if="field.fieldtype === 'Select'"
            type="select"
            :options="selectOptions(field)"
            :model-value="values[field.fieldname]"
            @update:model-value="(v) => (values[field.fieldname] = v)"
          />
          <FormControl
            v-else-if="field.fieldtype === 'Check'"
            type="checkbox"
            :label="__('Yes')"
            :model-value="Boolean(values[field.fieldname])"
            @update:model-value="(v) => (values[field.fieldname] = v ? 1 : 0)"
          />
          <FormControl
            v-else
            :type="
              ['Int', 'Float', 'Currency'].includes(field.fieldtype)
                ? 'number'
                : 'text'
            "
            :model-value="values[field.fieldname]"
            @update:model-value="(v) => (values[field.fieldname] = v)"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-2">
          <Button :label="__('Cancel')" @click="cancel" />
          <Button variant="solid" :label="__('Move')" @click="save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import AttachControl from '@/components/Controls/AttachControl.vue'
import { getFormat } from '@/utils'
import { Dialog, DatePicker, ErrorMessage, FormControl } from 'frappe-ui'
import { reactive, ref } from 'vue'

const props = defineProps({
  deal: { type: String, required: true },
  stageLabel: { type: String, default: '' },
  // [{ fieldname, label, fieldtype, options }] from crm.api.pipeline.get_missing_fields
  fields: { type: Array, default: () => [] },
})

const emit = defineEmits(['save', 'cancel'])

const show = defineModel({ type: Boolean })

const values = reactive({})
const error = ref('')
// The dialog's close event also fires after a save (while it animates out);
// without this flag it would cancel the move that save just retried.
let saved = false

function selectOptions(field) {
  return ['', ...(field.options || '').split('\n').filter(Boolean)].map(
    (o) => ({
      label: o ? __(o) : '',
      value: o,
    }),
  )
}

function isEmpty(value) {
  return value === undefined || value === null || value === ''
}

function cancel() {
  if (saved) return
  show.value = false
  error.value = ''
  emit('cancel')
}

function save() {
  // A Check is never "empty": unticked is a valid 0, so only blank inputs block.
  let missing = props.fields.filter(
    (f) => f.fieldtype !== 'Check' && isEmpty(values[f.fieldname]),
  )
  if (missing.length) {
    error.value = __('Fill in: {0}', [
      missing.map((f) => __(f.label)).join(', '),
    ])
    return
  }
  error.value = ''
  saved = true
  show.value = false
  let payload = {}
  for (let f of props.fields) {
    payload[f.fieldname] =
      f.fieldtype === 'Check' ? values[f.fieldname] || 0 : values[f.fieldname]
  }
  emit('save', payload)
}
</script>
