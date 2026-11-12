<template>
  <!-- Figma "Modal · Nova regra de distribuição" (2424:24981): four "Campo"
       fields and the gray footer of the shared modal shell. Creates the rule
       for every day of the week; conditions, schedule and priority stay in
       the full editor, which opens next. -->
  <Dialog v-model:open="show" :title="__('New distribution rule')">
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          class="field"
          v-model="name"
          type="text"
          :label="__('Name')"
          :placeholder="__('E.g. Website leads')"
        />
        <FormControl
          class="field"
          v-model="pipeline"
          type="select"
          :label="__('Funnel')"
          :options="pipelineOptions"
        />
        <FormControl
          class="field"
          v-model="rule"
          type="select"
          :label="__('How to distribute')"
          :options="ruleOptions"
        />
        <MultiSelect
          class="field"
          v-model="users"
          variant="outline"
          :label="__('People')"
          :options="userOptions"
          :placeholder="__('Choose the people')"
          :empty-text="__('No users found')"
        >
          <template #summary="{ summary }">
            <span class="truncate">{{ peopleLabel || summary }}</span>
          </template>
        </MultiSelect>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-between gap-3">
        <ErrorMessage :message="error" />
        <div class="ml-auto flex gap-3">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="__('Create rule')"
            :loading="saving"
            :disabled="!canCreate"
            @click="create"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { pipelinesStore } from '@/stores/pipelines'
import { usersStore } from '@/stores/users'
import { convertToConditions } from '@/utils'
import { storeToRefs } from 'pinia'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  MultiSelect,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const emit = defineEmits(['created'])
const show = defineModel({ type: Boolean })

const pipelineStore = pipelinesStore()
pipelineStore.ensureLoaded()
const { pipelines } = storeToRefs(pipelineStore)
const { users: allUsers, getUser } = usersStore()

const name = ref('')
const pipeline = ref('')
const rule = ref('Round Robin')
const users = ref([])
const saving = ref(false)
const error = ref('')

const ALL_DAYS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

const pipelineOptions = computed(() =>
  pipelines.value.map((p) => ({
    label: __(p.pipeline_name || p.name),
    value: p.name,
  })),
)

const ruleOptions = [
  { label: __('Round robin among the people'), value: 'Round Robin' },
  { label: __('By workload'), value: 'Load Balancing' },
]

const userOptions = computed(() =>
  (allUsers.data?.crmUsers || [])
    .filter((u) => u.name !== 'Administrator')
    .map((u) => ({ label: u.full_name || u.name, value: u.name })),
)

// "Rafael Lima, Juliana Prado, Carlos Menezes" (Figma) instead of "3 selected"
const peopleLabel = computed(() =>
  users.value.map((u) => getUser(u).full_name || u).join(', '),
)

const canCreate = computed(
  () => name.value.trim() && pipeline.value && users.value.length,
)

// a fresh form each time, on the first funnel
watch(show, (open) => {
  if (!open) return
  name.value = ''
  rule.value = 'Round Robin'
  users.value = []
  error.value = ''
  pipeline.value = pipelines.value[0]?.name || ''
})
watch(pipelineOptions, (options) => {
  if (show.value && !pipeline.value) pipeline.value = options[0]?.value || ''
})

// the list shows the description as "Como distribui"
function description() {
  let names = users.value.map((u) => getUser(u).full_name || u)
  let people =
    names.length > 1
      ? __('{0} and {1}', [names.slice(0, -1).join(', '), names.at(-1)])
      : names[0]
  return rule.value === 'Load Balancing'
    ? __('Load balancing among {0}', [people])
    : __('Round robin among {0}', [people])
}

async function create() {
  if (!canCreate.value) return
  saving.value = true
  error.value = ''
  const title = name.value.trim()
  const conditions = [['pipeline', 'equals', pipeline.value]]
  try {
    const doc = await call('frappe.client.insert', {
      doc: {
        doctype: 'Assignment Rule',
        name: title,
        assignment_rule_name: title,
        document_type: 'CRM Deal',
        rule: rule.value,
        priority: 1,
        disabled: 0,
        description: description(),
        users: users.value.map((user) => ({ user })),
        assignment_days: ALL_DAYS.map((day) => ({ day })),
        assign_condition: convertToConditions({ conditions }),
        assign_condition_json: JSON.stringify(conditions),
        unassign_condition: '',
        unassign_condition_json: '[]',
      },
    })
    toast.success(__('Assignment rule created'))
    show.value = false
    emit('created', doc)
  } catch (e) {
    error.value = e?.messages?.[0] || e?.message || __('Could not create')
  } finally {
    saving.value = false
  }
}
</script>
