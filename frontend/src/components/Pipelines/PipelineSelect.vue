<template>
  <div class="flex flex-col gap-1" data-testid="pipeline-select">
    <FormControl
      type="select"
      :label="label"
      :placeholder="__('Choose a funnel')"
      :options="options"
      :disabled="disabled"
      :model-value="modelValue || null"
      @update:model-value="(v) => emit('update:modelValue', v)"
    />
    <p v-if="description" class="text-p-sm text-ink-gray-4">
      {{ description }}
    </p>
  </div>
</template>
<script setup>
// Funnel picker for integrations (#70): where automatic entries (e-mail,
// Meta Lead Ads, calls, web forms) become cards. Lists the funnels the user
// can see, by name.
import { pipelinesStore } from '@/stores/pipelines'
import { storeToRefs } from 'pinia'
import { FormControl } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: () => __('Funnel') },
  description: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const pipelineStore = pipelinesStore()
const { pipelines } = storeToRefs(pipelineStore)
pipelineStore.ensureLoaded()

const options = computed(() =>
  pipelines.value.map((p) => ({ label: __(p.pipeline_name), value: p.name })),
)
</script>
