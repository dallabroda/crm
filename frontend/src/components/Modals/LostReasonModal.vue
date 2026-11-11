<template>
  <!-- Figma "Modal · Motivo da Perda" (1327:20065; "Outro" state 1876:24313):
       480px, "Informe o motivo", no description line, Style Guide "Campo"
       fields and a help line under the notes when the reason is "Outro" -->
  <Dialog
    v-model:open="show"
    size="ct-480"
    :title="__('Enter the reason')"
    @close="cancel"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <div class="ct-field-label">{{ __('Lost Reason') }} *</div>
          <Link
            ref="linkRef"
            class="form-control flex-1 truncate"
            :value="lostReason"
            doctype="CRM Lost Reason"
            :onCreate="onCreate"
            @change="(v) => (lostReason = v)"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="ct-field-label">
            {{ __('Lost Notes') }}{{ lostReason == 'Other' ? ' *' : '' }}
          </div>
          <!-- no `truncate` here: it kept the notes on one line -->
          <FormControl
            class="form-control flex-1"
            type="textarea"
            :value="lostNotes"
            @change="(e) => (lostNotes = e.target.value)"
          />
          <p
            v-if="lostReason == 'Other'"
            class="text-xs leading-4 text-ink-gray-6"
          >
            {{ __('Tell us why: with "Other", the note is required.') }}
          </p>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-3">
          <Button variant="outline" :label="__('Cancel')" @click="cancel" />
          <Button variant="solid" :label="__('Save')" @click="save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
import { createDocument } from '@/composables/document'
import { Dialog } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  doctype: { type: String, default: 'CRM Lead' },
  document: { type: Object, default: null },
})

const emit = defineEmits(['save', 'cancel'])

const show = defineModel({ type: Boolean })

const linkRef = ref(null)
const doc = props.document?.doc
const lostReason = ref(doc?.lost_reason || '')
const lostNotes = ref(doc?.lost_notes || '')
const error = ref('')

function cancel() {
  show.value = false
  error.value = ''
  lostReason.value = ''
  lostNotes.value = ''
  if (doc) {
    doc.status = props.document.originalDoc.status
  }
  emit('cancel')
}

function save() {
  if (!lostReason.value) {
    error.value = __('Lost Reason is required')
    return
  }
  if (lostReason.value === 'Other' && !lostNotes.value) {
    error.value = __('Lost Notes are required when Lost Reason is "Other"')
    return
  }

  error.value = ''
  show.value = false

  if (doc) {
    doc.lost_reason = lostReason.value
    doc.lost_notes = lostNotes.value
    props.document.save.submit()
  }
  emit('save', { lost_reason: lostReason.value, lost_notes: lostNotes.value })
  lostReason.value = ''
  lostNotes.value = ''
}

function onCreate(value, close) {
  let doc = { lost_reason: value }
  createDocument('CRM Lost Reason', doc, close, (doc) => {
    lostReason.value = doc.name
    linkRef.value?.reload('', true)
  })
}
</script>
