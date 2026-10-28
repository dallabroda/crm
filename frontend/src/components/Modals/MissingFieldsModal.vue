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
      <div class="flex flex-col gap-4">
        <div
          v-for="group in groups"
          :key="group.key"
          class="flex flex-col gap-2"
          :data-block="group.block"
        >
          <div
            v-if="groups.length > 1 || group.block !== 'Card'"
            class="text-base-medium text-ink-gray-8"
          >
            {{ group.title }}
          </div>
          <StageFields
            :fields="group.fields"
            :values="values"
            :docname="group.docname"
            @change="(f, v) => (values[f] = v)"
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
import StageFields from '@/components/Pipelines/StageFields.vue'
import { emptyRequiredFields } from '@/utils/pipelines'
import { Dialog, ErrorMessage } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  deal: { type: String, required: true },
  stageLabel: { type: String, default: '' },
  // [{ fieldname, label, fieldtype, options, block, block_label, docname }]
  // from crm.api.pipeline.get_missing_fields
  fields: { type: Array, default: () => [] },
})

// Fields of the card's organization, second organization or contact
// (credtech#196) are grouped by record and keyed by block, since the same
// field may be asked of two records (e.g. the website of both organizations)
const BLOCK_KEYS = {
  Card: 'card',
  Organization: 'organization',
  'Second organization': 'second_organization',
  Contact: 'contact',
}
const keyed = computed(() =>
  props.fields.map((f) => {
    let block = f.block || 'Card'
    return {
      ...f,
      block,
      field: f.fieldname,
      fieldname: block === 'Card' ? f.fieldname : `${block}|${f.fieldname}`,
    }
  }),
)
const byBlock = computed(() => keyed.value.some((f) => f.block !== 'Card'))
const groups = computed(() => {
  let groups = []
  for (let f of keyed.value) {
    let key = `${f.block}|${f.docname || props.deal}`
    let group = groups.find((g) => g.key === key)
    if (!group) {
      group = {
        key,
        block: f.block,
        docname: f.block === 'Card' ? props.deal : f.docname,
        title:
          f.block === 'Card'
            ? __('Card')
            : `${f.block_label || __(f.block)}: ${f.record_title || f.docname}`,
        fields: [],
      }
      groups.push(group)
    }
    group.fields.push(f)
  }
  return groups
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
  let missing = emptyRequiredFields(keyed.value, values)
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
  for (let f of keyed.value) {
    let value =
      f.fieldtype === 'Check' ? values[f.fieldname] || 0 : values[f.fieldname]
    if (!byBlock.value) {
      payload[f.field] = value
      continue
    }
    // by block: {card: {...}, organization: {...}, contact: {...}}
    let key = BLOCK_KEYS[f.block]
    payload[key] = { ...(payload[key] || {}), [f.field]: value }
  }
  emit('save', payload)
}
</script>
