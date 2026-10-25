<template>
  <Dialog v-model:open="show" :title="__('Move to another funnel')">
    <template #default>
      <div class="-mt-3 mb-4 text-p-base text-ink-gray-7">
        {{
          __('Field values are kept, even those the new funnel does not show.')
        }}
      </div>
      <div class="flex flex-col gap-3">
        <FormControl
          type="select"
          :label="__('Funnel')"
          :placeholder="__('Choose a funnel')"
          :options="pipelineOptions"
          :model-value="pipeline"
          @update:model-value="selectPipeline"
        />
        <FormControl
          type="select"
          :label="__('Stage')"
          :options="stageOptions"
          :disabled="!pipeline"
          :model-value="stage"
          @update:model-value="(v) => (stage = v)"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-2">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Move')"
            :loading="saving"
            :disabled="!pipeline || !stage"
            @click="save"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { pipelinesStore } from '@/stores/pipelines'
import { storeToRefs } from 'pinia'
import { Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  deal: { type: String, required: true },
  currentPipeline: { type: String, default: '' },
})

const emit = defineEmits(['moved'])

const show = defineModel({ type: Boolean })

const pipelineStore = pipelinesStore()
const { pipelines } = storeToRefs(pipelineStore)

const pipeline = ref('')
const stage = ref('')
const error = ref('')
const saving = ref(false)

const pipelineOptions = computed(() =>
  pipelines.value
    .filter((p) => p.name !== props.currentPipeline)
    .map((p) => ({ label: __(p.pipeline_name), value: p.name })),
)

const stageOptions = computed(() =>
  (pipelineStore.getPipeline(pipeline.value)?.stages || []).map((s) => ({
    label: __(s.deal_status),
    value: s.name,
  })),
)

// The server puts the card in the first stage, preferring open ones over
// won/lost; preselect the same so the user sees where it will land.
function selectPipeline(value) {
  pipeline.value = value
  let stages = pipelineStore.getPipeline(value)?.stages || []
  let open = stages.find((s) => !['Won', 'Lost'].includes(s.type))
  stage.value = (open || stages[0])?.name || ''
}

async function save() {
  error.value = ''
  saving.value = true
  try {
    let card = await pipelineStore.apiCall('change_pipeline', {
      deal: props.deal,
      pipeline: pipeline.value,
      stage: stage.value,
    })
    show.value = false
    emit('moved', card)
  } catch (e) {
    error.value =
      e?.messages?.[0] || __('Could not move the card to the other funnel.')
  } finally {
    saving.value = false
  }
}
</script>
