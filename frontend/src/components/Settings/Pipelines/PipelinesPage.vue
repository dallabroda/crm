<template>
  <PipelineEditor
    v-if="editing !== null"
    :pipeline="editing"
    :users="pipelineUsers"
    @back="closeEditor"
    @saved="onSaved"
  />
  <div v-else class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex w-9/12 flex-col gap-1">
        <h2 class="flex h-5 text-2xl-semibold leading-none">
          {{ __('Funnels') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Each funnel has its own stages, members and fields. Salespeople only see the funnels they are part of.',
            )
          }}
        </p>
      </div>
      <div class="flex w-3/12 items-center justify-end">
        <Button
          v-if="pipelineUsers.can_create"
          :label="__('New')"
          icon-left="lucide-plus"
          variant="solid"
          @click="editing = ''"
        />
      </div>
    </div>

    <div
      v-if="loading && !list.length"
      class="mt-12 flex items-center justify-center"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="w-full overflow-y-auto">
      <div class="flex items-center p-2 text-sm text-ink-gray-5">
        <div class="w-6/12">{{ __('Funnel') }}</div>
        <div class="w-2/12">{{ __('Stages') }}</div>
        <div class="w-2/12">{{ __('My role') }}</div>
        <div class="w-2/12">{{ __('Active') }}</div>
      </div>
      <div class="mx-2 h-px border-t border-outline-elevation-2" />
      <template v-for="(pipeline, i) in list" :key="pipeline.name">
        <div
          class="flex cursor-pointer items-center rounded-4 p-3 hover:bg-surface-sidebar"
          @click="editing = pipeline.name"
        >
          <div class="flex w-6/12 items-center gap-2">
            <IndicatorIcon :class="parseColor(pipeline.color)" />
            <span class="text-base-medium text-ink-gray-7">
              {{ __(pipeline.pipeline_name) }}
            </span>
          </div>
          <div class="w-2/12 text-base text-ink-gray-6">
            {{ pipeline.stages.length }}
          </div>
          <div class="w-2/12">
            <Badge :label="roleLabel(pipeline.my_role)" variant="subtle" />
          </div>
          <div class="w-2/12 text-base text-ink-gray-6">
            {{ pipeline.is_active ? __('Yes') : __('No') }}
          </div>
        </div>
        <hr v-if="list.length !== i + 1" class="mx-2" />
      </template>
    </div>
  </div>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PipelineEditor from './PipelineEditor.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { newPipelineRequested } from '@/composables/settings'
import { parseColor } from '@/utils'
import { Badge, LoadingIndicator, toast } from 'frappe-ui'
import { onMounted, ref, watch } from 'vue'

const pipelineStore = pipelinesStore()

// '' = new funnel, a name = edit that funnel, null = list
const editing = ref(null)
const list = ref([])
const loading = ref(false)
const pipelineUsers = ref({ can_create: false, is_admin: false, users: [] })

async function load() {
  loading.value = true
  try {
    let [pipelines, users] = await Promise.all([
      // admins also see inactive funnels here (the server ignores it for others)
      pipelineStore.apiCall('get_pipelines', { include_inactive: 1 }),
      pipelineStore.apiCall('get_pipeline_users'),
    ])
    list.value = pipelines || []
    pipelineUsers.value = users || pipelineUsers.value
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not load the funnels'))
  } finally {
    loading.value = false
  }
}

function roleLabel(role) {
  return (
    { Admin: __('Admin'), Owner: __('Owner'), Member: __('Salesperson') }[
      role
    ] || role
  )
}

function closeEditor() {
  editing.value = null
}

function onSaved() {
  editing.value = null
  load()
  // menu, Kanban and card pages read the funnels from the store
  pipelineStore.reload()
}

onMounted(load)

// "+" next to the funnels in the sidebar: open the editor of a new funnel
watch(
  newPipelineRequested,
  (requested) => {
    if (!requested) return
    newPipelineRequested.value = false
    editing.value = ''
  },
  { immediate: true },
)
</script>
