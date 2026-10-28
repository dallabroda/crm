<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2 pt-2">
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon="lucide-chevron-left"
          @click="emit('back')"
        />
        <h2 class="text-2xl-semibold leading-none">
          {{
            isNew ? __('New funnel') : __(form.pipeline_name) || __('Funnel')
          }}
        </h2>
        <Badge
          v-if="!canManage && !loading"
          :label="__('Read only')"
          variant="subtle"
        />
      </div>
      <Button
        v-if="canManage"
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </div>

    <div v-if="loading" class="mt-12 flex items-center justify-center">
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="flex flex-col gap-8 overflow-y-auto px-2 pb-6">
      <ErrorMessage v-if="error" :message="error" />

      <!-- Funnel -->
      <section class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <FormControl
          v-model="form.pipeline_name"
          :label="__('Name')"
          :disabled="!canManage"
          :placeholder="__('e.g. Sales, Credit, B2B')"
        />
        <FormControl
          type="select"
          :label="__('Color')"
          :options="colorOptions"
          :disabled="!canManage"
          :model-value="form.color"
          @update:model-value="(v) => (form.color = v)"
        />
        <div class="flex items-end gap-2 pb-1.5">
          <Switch v-model="isActive" :disabled="!canManage" />
          <span class="text-base text-ink-gray-7">{{ __('Active') }}</span>
        </div>
      </section>

      <!-- Stages -->
      <section class="flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <h3 class="text-lg-semibold text-ink-gray-8">{{ __('Stages') }}</h3>
          <Button
            v-if="canManage"
            :label="__('Add stage')"
            icon-left="lucide-plus"
            @click="addStage"
          />
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{ __('Drag to reorder. Won and Lost stages close the card.') }}
        </p>
        <Draggable
          :list="form.stages"
          item-key="_key"
          handle=".stage-handle"
          :disabled="!canManage"
          class="flex flex-col gap-2"
        >
          <template #item="{ element: stage, index }">
            <div
              class="flex items-center gap-2"
              :data-stage="stage.deal_status"
            >
              <span
                class="stage-handle lucide-grip-vertical size-4 cursor-grab text-ink-gray-4"
                :class="!canManage && 'invisible'"
              />
              <IndicatorIcon :class="parseColor(stage.color)" />
              <FormControl
                class="min-w-0 flex-1"
                :model-value="stage.deal_status"
                :disabled="!canManage"
                :placeholder="__('Stage name')"
                @update:model-value="(v) => (stage.deal_status = v)"
              />
              <!-- selects stretch to their container: fixed-width boxes keep the name visible -->
              <div class="w-36 shrink-0">
                <FormControl
                  type="select"
                  :options="typeOptions"
                  :disabled="!canManage"
                  :model-value="stage.type"
                  @update:model-value="(v) => (stage.type = v)"
                />
              </div>
              <div class="w-28 shrink-0">
                <FormControl
                  type="select"
                  :options="colorOptions"
                  :disabled="!canManage"
                  :model-value="stage.color"
                  @update:model-value="(v) => (stage.color = v)"
                />
              </div>
              <Button
                v-if="canManage"
                variant="ghost"
                icon="lucide-trash-2"
                :tooltip="__('Remove stage')"
                :aria-label="__('Remove stage')"
                @click="form.stages.splice(index, 1)"
              />
            </div>
          </template>
        </Draggable>
      </section>

      <!-- Members -->
      <section class="flex flex-col gap-2">
        <h3 class="text-lg-semibold text-ink-gray-8">{{ __('Members') }}</h3>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Owners see every card of the funnel and can change it. Salespeople see only their own cards.',
            )
          }}
        </p>
        <div
          v-for="(member, index) in form.members"
          :key="member.user"
          class="flex items-center gap-3"
          :data-member="member.user"
        >
          <UserAvatar :user="member.user" size="sm" />
          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
            {{ userName(member.user) }}
          </span>
          <div class="w-36 shrink-0">
            <FormControl
              type="select"
              :options="roleOptions(member.user, member.role)"
              :disabled="!canManage"
              :model-value="member.role"
              @update:model-value="(v) => (member.role = v)"
            />
          </div>
          <!-- system users (e.g. Administrator) are not in the users list: no role toggle -->
          <Tooltip
            v-if="users.is_admin && userInfo(member.user)"
            :text="__('Can create funnels and be an owner')"
          >
            <div class="flex items-center gap-1.5 text-sm text-ink-gray-6">
              <Switch
                size="sm"
                :model-value="Boolean(userInfo(member.user)?.pipeline_owner)"
                :disabled="Boolean(userInfo(member.user)?.is_admin)"
                @update:model-value="(v) => toggleOwnerRole(member.user, v)"
              />
              {{ __('Funnel owner role') }}
            </div>
          </Tooltip>
          <Button
            v-if="canManage"
            variant="ghost"
            icon="lucide-x"
            :tooltip="__('Remove member')"
            :aria-label="__('Remove member')"
            @click="form.members.splice(index, 1)"
          />
        </div>
        <div v-if="canManage && memberOptions.length" class="w-72">
          <FormControl
            type="select"
            :placeholder="__('Add member')"
            :options="memberOptions"
            :model-value="null"
            @update:model-value="addMember"
          />
        </div>
      </section>

      <PipelineDistribution
        v-model="form.distribution"
        :members="form.members"
        :field-options="distributionFieldOptions"
        :can-manage="canManage"
        :user-name="userName"
      />

      <!-- The card fields, their order and rules by stage moved to Form
           customization (credtech#180) -->
      <p class="text-p-sm text-ink-gray-5" data-testid="fields-moved">
        {{
          __(
            'The fields of the cards of this funnel, their order and the rules of each stage are set in Settings › Form customization.',
          )
        }}
      </p>
    </div>
  </div>
</template>

<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import PipelineDistribution from './PipelineDistribution.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { getMeta } from '@/stores/meta'
import { colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import {
  Badge,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  Tooltip,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  // '' = new funnel
  pipeline: { type: String, default: '' },
  // get_pipeline_users(): { can_create, is_admin, users: [...] }
  users: { type: Object, required: true },
})

const emit = defineEmits(['back', 'saved'])

const pipelineStore = pipelinesStore()

const isNew = computed(() => !props.pipeline)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const myRole = ref(null)
const catalog = ref([])

let keySeq = 0
const nextKey = () => `new-${++keySeq}`

const form = reactive({
  name: null,
  pipeline_name: '',
  color: 'blue',
  is_active: 1,
  stages: [],
  members: [],
  distribution: defaultDistribution(),
})

const canManage = computed(() =>
  isNew.value
    ? props.users.can_create
    : ['Admin', 'Owner'].includes(myRole.value),
)

const isActive = computed({
  get: () => Boolean(form.is_active),
  set: (v) => (form.is_active = v ? 1 : 0),
})

const colorOptions = colors.map((c) => ({ label: __(c), value: c }))
const typeOptions = [
  { label: __('Open'), value: 'Open' },
  { label: __('Ongoing'), value: 'Ongoing' },
  { label: __('On Hold'), value: 'On Hold' },
  { label: __('Won'), value: 'Won' },
  { label: __('Lost'), value: 'Lost' },
]

function defaultDistribution() {
  return {
    mode: 'round_robin',
    round_robin_users: [],
    rules: [],
    fallback: 'round_robin',
  }
}

// any card field can decide the salesperson (e.g. campaign, city, product)
// Rules test the incoming entry (a lead), so only fields that a lead has can
// decide; fields that exist only on the card would never match
const { getFields: getLeadFields } = getMeta('CRM Lead')
const distributionFieldOptions = computed(() => {
  let leadFields = new Set((getLeadFields() || []).map((f) => f.fieldname))
  return catalog.value
    .filter((f) => !f.disabled && leadFields.has(f.fieldname))
    .map((f) => ({ label: __(f.label), value: f.fieldname }))
})

function userInfo(user) {
  return props.users.users?.find((u) => u.name === user)
}

function userName(user) {
  return userInfo(user)?.full_name || user
}

function canOwn(user) {
  let info = userInfo(user)
  return Boolean(info?.pipeline_owner || info?.is_admin)
}

// an owner stays selectable even when the user list does not include them
// (system users such as Administrator)
function roleOptions(user, current) {
  return [
    { label: __('Salesperson'), value: 'Member' },
    ...(canOwn(user) || current === 'Owner'
      ? [{ label: __('Owner'), value: 'Owner' }]
      : []),
  ]
}

const memberOptions = computed(() =>
  (props.users.users || [])
    .filter((u) => !form.members.some((m) => m.user === u.name))
    .map((u) => ({ label: u.full_name || u.name, value: u.name })),
)

function addMember(user) {
  if (!user || form.members.some((m) => m.user === user)) return
  form.members.push({ user, role: 'Member' })
}

async function toggleOwnerRole(user, enabled) {
  try {
    let result = await pipelineStore.apiCall('set_pipeline_owner_role', {
      user,
      enabled: enabled ? 1 : 0,
    })
    let info = userInfo(user)
    if (info) info.pipeline_owner = result?.pipeline_owner ? 1 : 0
    if (!enabled) {
      let member = form.members.find((m) => m.user === user)
      if (member?.role === 'Owner') member.role = 'Member'
    }
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not change the role'))
  }
}

function addStage() {
  form.stages.push({
    _key: nextKey(),
    name: null,
    deal_status: '',
    type: form.stages.length ? 'Ongoing' : 'Open',
    color: colors[form.stages.length % colors.length],
  })
}

function validate() {
  if (!form.pipeline_name?.trim()) return __('Give the funnel a name.')
  if (!form.stages.length) return __('A funnel needs at least one stage.')
  let names = form.stages.map((s) => (s.deal_status || '').trim())
  if (names.some((n) => !n)) return __('Every stage needs a name.')
  let repeated = names.find((n, i) => names.indexOf(n) !== i)
  if (repeated) return __('Stage {0} appears more than once.', [repeated])
  return ''
}

function payload() {
  let doc = {
    pipeline_name: form.pipeline_name.trim(),
    color: form.color,
    is_active: form.is_active,
    stages: form.stages.map((s) => ({
      ...(s.name ? { name: s.name } : {}),
      deal_status: s.deal_status.trim(),
      type: s.type,
      color: s.color,
    })),
    // fields and rules are left out: Form customization saves them
    members: form.members.map((m) => ({ user: m.user, role: m.role })),
    distribution: {
      ...form.distribution,
      // incomplete rules are dropped; members who left the funnel too
      rules: form.distribution.rules.filter(
        (r) => r.field && r.user && form.members.some((m) => m.user === r.user),
      ),
      round_robin_users: form.distribution.round_robin_users.filter((u) =>
        form.members.some((m) => m.user === u),
      ),
    },
  }
  if (form.name) doc.name = form.name
  return doc
}

async function save() {
  error.value = validate()
  if (error.value) return
  saving.value = true
  try {
    let saved = await pipelineStore.apiCall('save_pipeline', { doc: payload() })
    // From here on the funnel and its new stages exist: a retry must update
    // them, never create them again
    adoptSavedKeys(saved)
    toast.success(__('Funnel saved'))
    emit('saved', saved)
  } catch (e) {
    error.value =
      e?.messages?.join('\n') || e?.message || __('Could not save the funnel')
  } finally {
    saving.value = false
  }
}

// The server saves stages in the order sent, so the n-th saved stage is the
// n-th stage of the form; new ones take their key.
function adoptSavedKeys(saved) {
  form.name = saved.name
  form.stages.forEach((stage, i) => {
    let key = saved.stages?.[i]?.name
    if (!stage.name && key) stage.name = key
  })
}

function fill(config) {
  form.name = config.name
  form.pipeline_name = config.pipeline_name
  form.color = config.color || 'blue'
  form.is_active = config.is_active ?? 1
  form.stages = (config.stages || []).map((s) => ({ ...s, _key: s.name }))
  form.members = (config.members || []).map((m) => ({
    user: m.user,
    role: m.role,
  }))
  form.distribution = {
    ...defaultDistribution(),
    ...(config.distribution || {}),
  }
  myRole.value = config.my_role
}

onMounted(async () => {
  loading.value = true
  try {
    let catalogData = await pipelineStore.apiCall('get_field_catalog')
    catalog.value = catalogData?.fields || []
    if (isNew.value) {
      addStage()
      return
    }
    fill(
      await pipelineStore.apiCall('get_pipeline_config', {
        pipeline: props.pipeline,
      }),
    )
  } catch (e) {
    error.value = e?.messages?.[0] || __('Could not load the funnel')
  } finally {
    loading.value = false
  }
})
</script>
