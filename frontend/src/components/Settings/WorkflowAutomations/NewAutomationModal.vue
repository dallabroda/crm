<template>
  <!-- Figma "Modal · Nova automação" (2424:24682): Nome, Quando, Se, Então in
       "Campo" fields and the gray footer of the shared modal shell. Creates
       a draft flow on the card; the builder opens next for the rest. -->
  <Dialog v-model:open="show" :title="__('New automation')">
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          class="field"
          v-model="title"
          type="text"
          :label="__('Name')"
          :placeholder="__('E.g. Task when reaching Proposal')"
        />
        <FormControl
          class="field"
          v-model="when"
          type="select"
          :label="__('When')"
          :options="whenOptions"
        />
        <FormControl
          class="field"
          v-model="stage"
          type="select"
          :label="__('If')"
          :options="stageOptions"
        />
        <FormControl
          class="field"
          v-model="then"
          type="select"
          :label="__('Then')"
          :options="thenOptions"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-3">
        <ErrorMessage :message="error" />
        <div class="ml-auto flex gap-3">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Create automation')"
            :loading="saving"
            :disabled="!title.trim()"
            @click="create"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { automationFlowDoc } from './newAutomation'
import { pipelinesStore } from '@/stores/pipelines'
import { storeToRefs } from 'pinia'
import { Button, Dialog, ErrorMessage, FormControl, call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const emit = defineEmits(['created'])
const show = defineModel({ type: Boolean })

const pipelineStore = pipelinesStore()
pipelineStore.ensureLoaded()
const { pipelines } = storeToRefs(pipelineStore)

const title = ref('')
const when = ref('stage')
const stage = ref('')
const then = ref('task')
const saving = ref(false)
const error = ref('')

const whenOptions = [
  { label: __('The card changes stage'), value: 'stage' },
  { label: __('A card is created'), value: 'created' },
  { label: __('A card is updated'), value: 'updated' },
  { label: __('Someone starts it from the card'), value: 'manual' },
]

// "Etapa = Proposta/Orçamento"; the funnel too when there are several
const stageOptions = computed(() => [
  { label: __('Any stage'), value: '' },
  ...pipelines.value.flatMap((p) =>
    (p.stages || []).map((s) => ({
      label:
        pipelines.value.length > 1
          ? __('Stage = {0} ({1})', [
              __(s.deal_status),
              __(p.pipeline_name || p.name),
            ])
          : __('Stage = {0}', [__(s.deal_status)]),
      value: s.name,
    })),
  ),
])

const thenOptions = [
  { label: __('Create a task for the owner'), value: 'task' },
  { label: __('Choose the steps in the editor'), value: 'editor' },
]

// a fresh form each time
watch(show, (open) => {
  if (!open) return
  title.value = ''
  when.value = 'stage'
  stage.value = ''
  then.value = 'task'
  error.value = ''
})

async function create() {
  if (!title.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const doc = await call('frappe.client.insert', {
      doc: automationFlowDoc({
        title: title.value.trim(),
        when: when.value,
        stage: stage.value,
        then: then.value,
        taskTitle: __('Follow up on {0}', [
          '{{ doc.deal_name or doc.name }}',
        ]),
      }),
    })
    show.value = false
    emit('created', doc)
  } catch (e) {
    error.value = e?.messages?.[0] || e?.message || __('Could not create')
  } finally {
    saving.value = false
  }
}
</script>
