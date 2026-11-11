<template>
  <!-- Figma "Configurações · Funis · Campos do card" (2324:15315): the card
       fields of this funnel, under the editor's title and tabs -->
  <FormCustomizationPage
    v-if="tab === 'fields' && form.name"
    :funnel="form.name"
  >
    <template #title>
      <SettingsBackTitle :title="title" @back="emit('back')" />
    </template>
    <template #tabs>
      <SettingsTabs v-model="tab" class="flex-1" :tabs="tabs" />
    </template>
  </FormCustomizationPage>
  <div v-else class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="title">
      <template #badge>
        <Badge
          v-if="!canManage && !loading"
          :label="__('Read only')"
          variant="subtle"
        />
      </template>
      <template #title>
        <SettingsBackTitle :title="title" @back="emit('back')" />
      </template>
      <template #actions>
        <Button
          v-if="canManage"
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          @click="save"
        />
      </template>
    </SettingsPageHeader>

    <!-- Figma "Abas e ação" (2339:10530): Etapas, Membros, Campos do card -->
    <div class="shrink-0 border-b border-[var(--ct-border-soft)]">
      <SettingsTabs v-model="tab" :tabs="tabs" />
    </div>

    <div v-if="loading" class="mt-12 flex items-center justify-center">
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="flex flex-col gap-6 overflow-y-auto pb-6">
      <ErrorMessage v-if="error" :message="error" />

      <template v-if="tab === 'stages'">
        <!-- Figma "Dados do funil": name, color (200px) and Active -->
        <section class="flex h-20 items-start gap-4">
          <div class="ct-field-48 min-w-0 flex-1">
            <FormControl
              v-model="form.pipeline_name"
              variant="outline"
              size="lg"
              :label="__('Funnel name')"
              :disabled="!canManage"
              :placeholder="__('e.g. Sales, Credit, B2B')"
            />
          </div>
          <div class="ct-field-48 w-[200px] shrink-0">
            <FormControl
              type="select"
              variant="outline"
              size="lg"
              :label="__('Color')"
              :options="colorOptions"
              :disabled="!canManage"
              :model-value="form.color"
              @update:model-value="(v) => (form.color = v)"
            />
          </div>
          <div class="mt-12 flex h-5 shrink-0 items-center gap-2">
            <Switch v-model="isActive" size="md" :disabled="!canManage" />
            <span class="text-[14px] leading-5 text-[var(--ct-text-primary)]">
              {{ __('Active') }}
            </span>
          </div>
        </section>

        <!-- Stages: Figma "Cabeçalho das etapas" and "Tabela" -->
        <section class="flex flex-col gap-6">
          <div class="flex items-center justify-between gap-3 pt-4">
            <h3
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Stages') }}
            </h3>
            <Button
              v-if="canManage"
              variant="outline"
              :label="__('Add stage')"
              icon-left="lucide-plus"
              @click="addStage"
            />
          </div>
          <div class="ct-table">
            <div class="ct-table-head" :style="stageColumns">
              <div>{{ __('Order') }}</div>
              <div>{{ __('Stage') }}</div>
              <div>{{ __('Status of the card') }}</div>
              <div />
            </div>
            <Draggable
              :list="form.stages"
              item-key="_key"
              handle=".stage-handle"
              :disabled="!canManage"
            >
              <template #item="{ element: stage, index }">
                <div
                  class="ct-table-row group h-[52px]"
                  :style="stageColumns"
                  :data-stage="stage.deal_status"
                >
                  <!-- drag by the order number -->
                  <div
                    class="stage-handle flex items-center gap-2 font-medium text-[var(--ct-text-primary)]"
                    :class="canManage && 'cursor-grab'"
                    :title="canManage ? __('Drag to reorder') : ''"
                  >
                    {{ index + 1 }}
                    <span
                      v-if="canManage"
                      class="lucide-grip-vertical size-4 text-ink-gray-4 opacity-0 group-hover:opacity-100"
                    />
                  </div>
                  <div class="flex items-center gap-2">
                    <Dropdown
                      v-if="canManage"
                      :options="stageColorOptions(stage)"
                    >
                      <button
                        type="button"
                        class="size-2 shrink-0 rounded-full bg-current"
                        :class="parseColor(stage.color)"
                        :aria-label="__('Color')"
                      />
                    </Dropdown>
                    <span
                      v-else
                      class="size-2 shrink-0 rounded-full bg-current"
                      :class="parseColor(stage.color)"
                    />
                    <input
                      v-model="stage.deal_status"
                      class="h-7 min-w-0 flex-1 rounded-[6px] border-0 bg-transparent px-1 -ml-1 text-[14px] font-medium leading-5 text-[var(--ct-text-primary)] placeholder-ink-gray-4 hover:bg-[var(--ct-bg-soft)] focus:bg-[var(--ct-bg-page)] focus:ring-1 focus:ring-[var(--ct-border-strong)] disabled:hover:bg-transparent"
                      :disabled="!canManage"
                      :placeholder="__('Stage name')"
                    />
                  </div>
                  <div class="flex">
                    <Dropdown
                      v-if="canManage"
                      :options="stageTypeOptions(stage)"
                    >
                      <button type="button" :class="typePill(stage.type)">
                        {{ typeLabel(stage.type) }}
                      </button>
                    </Dropdown>
                    <span v-else :class="typePill(stage.type)">
                      {{ typeLabel(stage.type) }}
                    </span>
                  </div>
                  <div class="flex">
                    <Button
                      v-if="canManage"
                      variant="subtle"
                      :label="__('Remove')"
                      :aria-label="__('Remove stage')"
                      @click="form.stages.splice(index, 1)"
                    />
                  </div>
                </div>
              </template>
            </Draggable>
          </div>
        </section>

        <!-- the card's second organization in this funnel (credtech#195);
             not in the Figma -->
        <section class="ct-field-48 flex items-start gap-4">
          <div class="min-w-0 flex-1">
            <FormControl
              v-model="form.second_organization_label"
              variant="outline"
              size="lg"
              :label="__('Name of the second organization')"
              :disabled="!canManage"
              :placeholder="__('Second organization')"
              :description="__('e.g. Debtor, Guarantor')"
            />
          </div>
          <div class="min-w-0 flex-1">
            <FormControl
              type="select"
              variant="outline"
              size="lg"
              :label="__('Contacts of cards with two organizations')"
              :options="contactsFromOptions"
              :disabled="!canManage"
              :model-value="form.default_contacts_from"
              @update:model-value="(v) => (form.default_contacts_from = v)"
            />
          </div>
        </section>
      </template>

      <template v-else-if="tab === 'members'">
        <p class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
          {{
            __(
              'Who works in this funnel. Salespeople only see the funnels they take part in; owners can also change the stages and the fields.',
            )
          }}
        </p>
        <!-- Figma "Cabeçalho": "N pessoas" and "Adicionar pessoa" -->
        <div class="flex items-center justify-between gap-3">
          <h3
            class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
          >
            {{
              form.members.length === 1
                ? __('1 person')
                : __('{0} people', [form.members.length])
            }}
          </h3>
          <Dropdown v-if="canManage" :options="addMemberOptions">
            <Button
              variant="outline"
              :label="__('Add person')"
              icon-left="lucide-plus"
              :disabled="!memberOptions.length"
            />
          </Dropdown>
        </div>
        <div class="ct-table">
          <div class="ct-table-head" :style="memberColumns">
            <div>{{ __('Person') }}</div>
            <div>{{ __('Role in the funnel') }}</div>
            <div />
          </div>
          <div
            v-for="(member, index) in form.members"
            :key="member.user"
            class="ct-table-row h-[52px]"
            :style="memberColumns"
            :data-member="member.user"
          >
            <div class="flex items-center gap-2">
              <UserAvatar :user="member.user" size="xl" hide-status />
              <div class="flex min-w-0 flex-col">
                <span class="ct-table-name">
                  {{
                    member.user === currentUser
                      ? __('You')
                      : userName(member.user)
                  }}
                </span>
                <span
                  class="truncate text-[12px] leading-4 text-[var(--ct-text-tertiary)]"
                >
                  {{ member.user }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <Dropdown v-if="canManage" :options="memberRoleOptions(member)">
                <button type="button" class="ct-pill">
                  {{ roleLabel(member.role) }}
                </button>
              </Dropdown>
              <span v-else class="ct-pill">{{ roleLabel(member.role) }}</span>
              <!-- system users (e.g. Administrator) are not in the users list:
                   no role toggle. Not in the Figma. -->
              <Tooltip
                v-if="users.is_admin && userInfo(member.user)"
                :text="__('Can create funnels and be an owner')"
              >
                <div class="flex items-center gap-1.5 text-sm text-ink-gray-6">
                  <Switch
                    size="sm"
                    :model-value="
                      Boolean(userInfo(member.user)?.pipeline_owner)
                    "
                    :disabled="Boolean(userInfo(member.user)?.is_admin)"
                    @update:model-value="(v) => toggleOwnerRole(member.user, v)"
                  />
                  {{ __('Funnel owner role') }}
                </div>
              </Tooltip>
            </div>
            <div class="flex">
              <Button
                v-if="canManage"
                variant="subtle"
                :label="__('Remove')"
                :aria-label="__('Remove member')"
                @click="form.members.splice(index, 1)"
              />
            </div>
          </div>
        </div>

        <!-- not in the Figma: who receives the leads that arrive by themselves -->
        <PipelineDistribution
          v-model="form.distribution"
          class="pt-4"
          :members="form.members"
          :field-options="distributionFieldOptions"
          :can-manage="canManage"
          :user-name="userName"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsBackTitle from '@/components/Settings/SettingsBackTitle.vue'
import SettingsTabs from '@/components/Settings/SettingsTabs.vue'
import FormCustomizationPage from '@/components/Settings/FormCustomization/FormCustomizationPage.vue'
import '@/components/Settings/settingsTable.css'
import '@/components/Settings/fieldOutline.css'
import UserAvatar from '@/components/UserAvatar.vue'
import PipelineDistribution from './PipelineDistribution.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { getMeta } from '@/stores/meta'
import { sessionStore } from '@/stores/session'
import { colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import {
  Badge,
  Dropdown,
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
const { user: currentUser } = sessionStore()

// Figma "Configurações · Funis · Etapas / Membros / Campos do card"
// (2339:10530, 2339:10998, 2324:15315); a new funnel gets its fields once saved
const tab = ref('stages')
const tabs = computed(() => [
  { label: __('Stages'), value: 'stages' },
  { label: __('Members'), value: 'members' },
  ...(isNew.value ? [] : [{ label: __('Card fields'), value: 'fields' }]),
])
const title = computed(() =>
  isNew.value ? __('New funnel') : __(form.pipeline_name) || __('Funnel'),
)

// Figma column widths at 1440px (Ordem 102, Etapa 508, Situação 284; Pessoa
// 610, Papel 284), kept in proportion on other widths
const stageColumns = {
  gridTemplateColumns:
    'minmax(0,102fr) minmax(0,508fr) minmax(0,284fr) minmax(92px,104fr)',
}
const memberColumns = {
  gridTemplateColumns: 'minmax(0,610fr) minmax(0,284fr) minmax(92px,120fr)',
}
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
  second_organization_label: '',
  default_contacts_from: 'Organization',
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
const contactsFromOptions = [
  { label: __('Organization'), value: 'Organization' },
  { label: __('Second organization'), value: 'Second organization' },
  { label: __('Both'), value: 'Both' },
]
const typeOptions = [
  { label: __('Open'), value: 'Open' },
  { label: __('Ongoing'), value: 'Ongoing' },
  { label: __('On Hold'), value: 'On Hold' },
  { label: __('Won'), value: 'Won' },
  { label: __('Lost'), value: 'Lost' },
]

// Figma "Pílula de status" of "Situação do card"
const TYPE_PILLS = {
  Open: 'ct-pill ct-pill-dot',
  Ongoing: 'ct-pill ct-pill-dot ct-pill-blue',
  'On Hold': 'ct-pill ct-pill-dot ct-pill-amber',
  Won: 'ct-pill ct-pill-dot ct-pill-green',
  Lost: 'ct-pill ct-pill-dot ct-pill-red',
}
function typePill(type) {
  return TYPE_PILLS[type] || TYPE_PILLS.Open
}
function typeLabel(type) {
  if (type === 'Open') return __('Open', null, 'card status')
  return typeOptions.find((o) => o.value === type)?.label || type
}
function stageTypeOptions(stage) {
  return typeOptions.map((o) => ({
    label: o.value === 'Open' ? __('Open', null, 'card status') : o.label,
    onClick: () => (stage.type = o.value),
  }))
}
function stageColorOptions(stage) {
  return colorOptions.map((o) => ({
    label: o.label,
    onClick: () => (stage.color = o.value),
  }))
}

function roleLabel(role) {
  return roleOptions(null, role).find((o) => o.value === role)?.label || role
}
function memberRoleOptions(member) {
  return roleOptions(member.user, member.role).map((o) => ({
    label: o.label,
    onClick: () => (member.role = o.value),
  }))
}
const addMemberOptions = computed(() =>
  memberOptions.value.map((o) => ({
    label: o.label,
    onClick: () => addMember(o.value),
  })),
)

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
    second_organization_label: (form.second_organization_label || '').trim(),
    default_contacts_from: form.default_contacts_from || 'Organization',
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
  form.second_organization_label = config.second_organization_label || ''
  form.default_contacts_from = config.default_contacts_from || 'Organization'
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
    // fields that moved to the organization still come with the lead, so rules can test them
    catalog.value = [
      ...(catalogData?.fields || []),
      ...(catalogData?.moved || []),
    ]
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

<style scoped>
/* Figma "Campo" (2339:10530, 2324:15315): the label is 20px tall, 6px over
   the 48px box */
.ct-field-48 :deep(label) {
  line-height: 20px;
}
</style>
