<template>
  <PipelineEditor
    v-if="editing !== null"
    :pipeline="editing"
    :users="pipelineUsers"
    @back="closeEditor"
    @saved="onSaved"
  />
  <div v-else class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Funnels')">
      <template #description>
        {{
          __(
            'Each funnel has its own stages, members and fields. Salespeople only see the funnels they are part of.',
          )
        }}
      </template>
      <template #actions>
        <template v-if="pipelineUsers.can_create">
          <Button
            v-if="pipelineUsers.can_create"
            :label="__('New funnel')"
            icon-left="lucide-plus"
            variant="solid"
            @click="editing = ''"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <div
      v-if="loading && !list.length"
      class="mt-12 flex items-center justify-center"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <!-- Figma "Configurações · Funis" (2324:14511): "Tabela de funis" with
         56px rows, then the global fields of contacts and organizations -->
    <template v-else>
      <div class="ct-table shrink-0">
        <div class="ct-table-head" :style="columns">
          <div>{{ __('Funnel') }}</div>
          <div>{{ __('Stages') }}</div>
          <div>{{ __('My role') }}</div>
          <div>{{ __('Active') }}</div>
        </div>
        <div
          v-for="pipeline in list"
          :key="pipeline.name"
          class="ct-table-row h-14 cursor-pointer hover:bg-[var(--ct-bg-soft)]"
          :style="columns"
          @click="editing = pipeline.name"
        >
          <div class="flex items-center gap-2">
            <span
              class="size-2 shrink-0 rounded-full bg-current"
              :class="parseColor(pipeline.color)"
            />
            <span class="ct-table-name">{{ __(pipeline.pipeline_name) }}</span>
          </div>
          <div>{{ pipeline.stages.length }}</div>
          <div class="flex">
            <span class="ct-pill">{{ roleLabel(pipeline.my_role) }}</span>
          </div>
          <div>{{ pipeline.is_active ? __('Yes') : __('No') }}</div>
        </div>
      </div>
      <div
        class="flex shrink-0 items-center gap-3 rounded-[8px] bg-[var(--ct-bg-soft)] p-4"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span
            class="text-[14px] font-medium leading-5 text-[var(--ct-text-primary)]"
          >
            {{ __('Contacts and Organizations fields') }}
          </span>
          <span class="text-[12px] leading-4 text-[var(--ct-text-tertiary)]">
            {{
              __(
                'They apply to every funnel. The card fields are inside each funnel.',
              )
            }}
          </span>
        </div>
        <Button
          variant="outline"
          class="bg-[var(--ct-bg-page)]"
          :label="__('Edit fields')"
          @click="
            router.push({
              name: 'Settings',
              params: { section: 'form-customization' },
            })
          "
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import PipelineEditor from './PipelineEditor.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { newPipelineRequested } from '@/composables/settings'
import { parseColor } from '@/utils'
import { useRouter } from 'vue-router'
import '@/components/Settings/settingsTable.css'
import { LoadingIndicator, toast } from 'frappe-ui'
import { onMounted, ref, watch } from 'vue'

const pipelineStore = pipelinesStore()
const router = useRouter()

// '' = new funnel, a name = edit that funnel, null = list
const editing = ref(null)
const list = ref([])
const loading = ref(false)
const pipelineUsers = ref({ can_create: false, is_admin: false, users: [] })

// Figma column widths at 1440px (Funil 508, Etapas 152, Meu papel 203,
// Ativo 135), kept in proportion on other widths
const columns = {
  gridTemplateColumns:
    'minmax(0,508fr) minmax(0,152fr) minmax(0,203fr) minmax(0,135fr)',
}

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
