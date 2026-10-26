<template>
  <div class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4">
    <div class="flex items-start justify-between gap-4">
      <div class="flex flex-col gap-1">
        <div class="text-base-semibold text-ink-gray-9">
          {{ __('Google Ads, website and other tools') }}
        </div>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'Each source gets its own address and key. Leads arrive the moment the form is sent, with the campaign that brought them.',
            )
          }}
        </p>
      </div>
      <Dropdown :options="addOptions" align="end">
        <Button
          variant="solid"
          :label="__('Add source')"
          icon-left="lucide-plus"
          :loading="creating"
        />
      </Dropdown>
    </div>

    <!-- name and funnel of the source being added -->
    <div
      v-if="draft"
      class="flex items-end gap-3 rounded border border-outline-gray-1 p-3"
    >
      <div class="flex-1">
        <FormControl
          v-model="draft.label"
          type="text"
          :label="__('Name')"
          :placeholder="sourceType(draft.type).label"
        />
      </div>
      <div class="w-56">
        <PipelineSelect v-model="draft.pipeline" />
      </div>
      <Button :label="__('Cancel')" @click="draft = null" />
      <Button
        variant="solid"
        :label="__('Create')"
        :disabled="!draft.pipeline"
        :loading="creating"
        @click="create"
      />
    </div>

    <p
      v-if="!loading && !sources.length && !draft"
      class="text-p-sm text-ink-gray-5"
    >
      {{ __('No source added yet.') }}
    </p>
    <WebhookSource
      v-for="source in sources"
      :key="source.name"
      :source="source"
      :initial-key="keys[source.name] || ''"
      @changed="load"
    />
  </div>
</template>

<script setup>
import PipelineSelect from '@/components/Pipelines/PipelineSelect.vue'
import WebhookSource from './WebhookSource.vue'
import {
  SOURCE_TYPES,
  sourceType,
  webhookSourcesApi,
} from './webhookSourcesApi'
import { Button, Dropdown, FormControl, toast } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const emit = defineEmits(['changed'])

const sources = ref([])
const loading = ref(false)
const creating = ref(false)
const draft = ref(null)
// key of a source created in this visit, shown once in its row
const keys = ref({})

const addOptions = computed(() =>
  SOURCE_TYPES.map((t) => ({
    label: t.label,
    icon: t.icon,
    onClick: () => (draft.value = { type: t.value, label: '', pipeline: '' }),
  })),
)

async function load() {
  loading.value = true
  try {
    sources.value = (await webhookSourcesApi.list()) || []
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the lead sources'))
  } finally {
    loading.value = false
  }
  emit('changed')
}

async function create() {
  creating.value = true
  try {
    let { type, label, pipeline } = draft.value
    let created = await webhookSourcesApi.create(
      type,
      label.trim() || sourceType(type).label,
      pipeline,
    )
    keys.value[created.name] = created.key
    draft.value = null
    await load()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not create the source'))
  } finally {
    creating.value = false
  }
}

onMounted(load)
</script>
