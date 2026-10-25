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
      <StageFields
        :fields="fields"
        :values="values"
        :docname="deal"
        @change="(f, v) => (values[f] = v)"
      />
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
import StageFields from '@/components/Pipelines/StageFields.vue'
import { emptyRequiredFields } from '@/utils/pipelines'
import { Dialog, ErrorMessage } from 'frappe-ui'
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

function cancel() {
  if (saved) return
  show.value = false
  error.value = ''
  emit('cancel')
}

function save() {
  let missing = emptyRequiredFields(props.fields, values)
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
