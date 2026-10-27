<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="field in fields"
      :key="field.fieldname"
      :data-stage-field="field.fieldname"
    >
      <div class="mb-2 text-sm text-ink-gray-5">
        {{ __(field.label) }}
        <span v-if="isRequired(field)" class="text-ink-red-4">*</span>
      </div>
      <Link
        v-if="field.fieldtype === 'Link'"
        class="form-control flex-1 truncate"
        :value="values[field.fieldname]"
        :doctype="field.options"
        @change="(v) => emit('change', field.fieldname, v)"
      />
      <DatePicker
        v-else-if="field.fieldtype === 'Date'"
        :model-value="values[field.fieldname]"
        variant="outline"
        :format="getFormat('', '', true, false, false)"
        @change="(v) => emit('change', field.fieldname, v)"
      />
      <AttachControl
        v-else-if="field.fieldtype === 'Attach'"
        :value="values[field.fieldname]"
        doctype="CRM Deal"
        :docname="docname"
        :fieldname="field.fieldname"
        @change="(v) => emit('change', field.fieldname, v)"
      />
      <FormControl
        v-else-if="field.fieldtype === 'Select'"
        type="select"
        :options="selectOptions(field)"
        :model-value="values[field.fieldname]"
        @update:model-value="(v) => emit('change', field.fieldname, v)"
      />
      <FormControl
        v-else-if="field.fieldtype === 'Check'"
        type="checkbox"
        :label="isRequired(field) ? __('Tick to confirm') : __('Yes')"
        :model-value="Boolean(values[field.fieldname])"
        @update:model-value="(v) => emit('change', field.fieldname, v ? 1 : 0)"
      />
      <FormControl
        v-else
        :type="
          ['Int', 'Float', 'Currency'].includes(field.fieldtype)
            ? 'number'
            : 'text'
        "
        :model-value="values[field.fieldname]"
        @update:model-value="(v) => emit('change', field.fieldname, v)"
      />
    </div>
  </div>
</template>
<script setup>
// Inputs for a funnel's card fields (#72, credtech#179): the required ones when
// moving a card (MissingFieldsModal) and the card fields when creating one
// (DealModal). Writes into `values`.
import Link from '@/components/Controls/Link.vue'
import AttachControl from '@/components/Controls/AttachControl.vue'
import { getFormat } from '@/utils'
import { DatePicker, FormControl } from 'frappe-ui'

defineProps({
  // [{ fieldname, label, fieldtype, options, required? }]
  fields: { type: Array, default: () => [] },
  // current values (the card's doc or a local draft); changes go out as events
  values: { type: Object, required: true },
  // card name, for attachments (empty while creating)
  docname: { type: String, default: '' },
})

const emit = defineEmits(['change'])

// fields without `required` come from MissingFieldsModal: all of them are required
function isRequired(field) {
  return field.required === undefined || Boolean(field.required)
}

function selectOptions(field) {
  return ['', ...(field.options || '').split('\n').filter(Boolean)].map(
    (o) => ({ label: o ? __(o) : '', value: o }),
  )
}
</script>
