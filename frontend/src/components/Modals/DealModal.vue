<template>
  <Dialog v-model:open="show" :size="'3xl'" bare>
    <template #default>
      <div class="bg-surface-elevation-2 px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <Dialog.Title as-child>
              <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
                {{ __('Create Deal') }}
              </h3>
            </Dialog.Title>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Dialog.Close as-child>
              <Button
                :aria-label="__('Close')"
                variant="ghost"
                class="w-7"
                icon="lucide-x"
              />
            </Dialog.Close>
          </div>
        </div>
        <div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <div
              v-if="hasOrganizationSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Organization') }}</div>
              <Switch v-model="chooseExistingOrganization" />
            </div>
            <div
              v-if="hasContactSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Contact') }}</div>
              <Switch v-model="chooseExistingContact" />
            </div>
          </div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="h-px w-full border-t my-5"
          />
          <div
            v-if="usePipelines"
            class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <FormControl
              type="select"
              :label="__('Funnel')"
              :options="pipelineOptions"
              :model-value="deal.doc.pipeline"
              @update:model-value="selectPipeline"
            />
            <FormControl
              type="select"
              :label="__('Stage')"
              :options="stageOptions"
              :model-value="deal.doc.status"
              @update:model-value="(v) => (deal.doc.status = v)"
            />
          </div>
          <div
            v-if="stageFields.length"
            class="mb-4 rounded-6 border border-outline-gray-2 p-3"
            data-testid="stage-required-fields"
          >
            <div class="mb-3 text-sm text-ink-gray-6">
              {{ __('Card fields') }}
            </div>
            <StageFields
              :fields="stageFields"
              :values="deal.doc"
              @change="(f, v) => (deal.doc[f] = v)"
            />
          </div>
          <FieldLayout
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="deal.doc"
            doctype="CRM Deal"
          />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isDealCreating"
            @click="createDeal"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { pipelinesStore } from '@/stores/pipelines'
import StageFields from '@/components/Pipelines/StageFields.vue'
import { emptyRequiredFields } from '@/utils/pipelines'
import { storeToRefs } from 'pinia'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { useTelemetry } from '@framework/ui/telemetry'
import { useCrmOnboarding } from '@/composables/onboarding'
import { Dialog, FormControl, Switch, call, createResource } from 'frappe-ui'
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: { type: Object, default: () => ({}) },
})

const { getUser, isManager } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const show = defineModel({ type: Boolean })
const router = useRouter()
const error = ref(null)

const { document: deal, triggerOnBeforeCreate } = useDocument('CRM Deal')

const hasOrganizationSections = ref(true)
const hasContactSections = ref(true)

const isDealCreating = ref(false)
const chooseExistingContact = ref(false)
const chooseExistingOrganization = ref(false)
const { capture } = useTelemetry()
const { completeStep } = useCrmOnboarding()

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Deal'],
  params: { doctype: 'CRM Deal', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    hasOrganizationSections.value = false
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          if (
            ['organization_section', 'organization_details_section'].includes(
              section.name,
            )
          ) {
            hasOrganizationSections.value = true
          } else if (
            ['contact_section', 'contact_details_section'].includes(
              section.name,
            )
          ) {
            hasContactSections.value = true
          }
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = dealStatuses.value
              field.prefix = getDealStatus(deal.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              deal.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

watch(
  [chooseExistingOrganization, chooseExistingContact, () => tabs.data],
  ([organization, contact]) => {
    tabs.data?.forEach((tab) => {
      tab.sections.forEach((section) => {
        if (section.name === 'organization_section') {
          section.hidden = !organization
        } else if (section.name === 'organization_details_section') {
          section.hidden = organization
        } else if (section.name === 'contact_section') {
          section.hidden = !contact
        } else if (section.name === 'contact_details_section') {
          section.hidden = contact
        }
      })
    })
  },
  { immediate: true },
)

const dealStatuses = computed(() => statusOptions('deal'))

// Funnels (#72): the card is created in a funnel and one of its stages; the
// layout's own status field is replaced by the selects above
const pipelineStore = pipelinesStore()
const { pipelines } = storeToRefs(pipelineStore)
const usePipelines = computed(() => pipelines.value.length > 0)

const pipelineOptions = computed(() =>
  pipelines.value.map((p) => ({ label: __(p.pipeline_name), value: p.name })),
)

const stageOptions = computed(() =>
  (pipelineStore.getPipeline(deal.doc.pipeline)?.stages || []).map((s) => ({
    label: __(s.deal_status),
    value: s.name,
  })),
)

// Same rule as the server: first open stage, else the first one
function firstStage(pipeline) {
  let stages = pipelineStore.getPipeline(pipeline)?.stages || []
  return (stages.find((s) => !['Won', 'Lost'].includes(s.type)) || stages[0])
    ?.name
}

function selectPipeline(pipeline) {
  deal.doc.pipeline = pipeline
  deal.doc.status = firstStage(pipeline)
}

function eachField(callback) {
  tabs.data?.forEach((tab) =>
    tab.sections.forEach((section) =>
      section.columns.forEach((column) => column.fields.forEach(callback)),
    ),
  )
}

watch([usePipelines, () => tabs.data], ([inUse]) => {
  eachField((field) => {
    if (field.fieldname === 'status') field.hidden = inUse ? 1 : 0
  })
})

// Card fields of the chosen funnel and stage (dynamic forms, credtech#179), in
// the funnel order, created fields included; the required ones are marked and
// the server refuses the card without them. Those the quick entry already has
// are filled there.
const stageRequired = ref([])
let stageRequest = 0
watch(
  () => [deal.doc.pipeline, deal.doc.status],
  async ([pipeline, stage]) => {
    let request = ++stageRequest
    if (!usePipelines.value || !pipeline || !stage) {
      stageRequired.value = []
      return
    }
    try {
      let schema = await call('crm.api.forms.get_form_schema', {
        doctype: 'CRM Deal',
        pipeline,
        stage,
      })
      if (request !== stageRequest) return
      stageRequired.value = (schema?.fields || [])
        .filter((f) => f.visible && !f.locked)
        .map((f) => ({
          fieldname: f.fieldname,
          label: f.label,
          fieldtype: f.fieldtype,
          // StageFields takes the options as text, one per line
          options: Array.isArray(f.options)
            ? f.options.map((o) => o.value).join('\n')
            : f.options || '',
          required: f.required ? 1 : 0,
        }))
    } catch (e) {
      if (request === stageRequest) stageRequired.value = []
      console.error('[pipelines] could not load the stage rules', e)
    }
  },
)

const quickEntryFieldnames = computed(() => {
  let names = new Set()
  eachField((field) => !field.hidden && names.add(field.fieldname))
  return names
})

// asked in the box above; those already in the quick entry are filled there
const stageFields = computed(() =>
  stageRequired.value.filter(
    (f) => !quickEntryFieldnames.value.has(f.fieldname),
  ),
)

// Existing contact: only the chosen organization's contacts (#72)
watch(
  [() => deal.doc.organization, () => tabs.data],
  ([organization]) => {
    eachField((field) => {
      if (field.fieldname === 'contact') {
        field.link_filters = organization
          ? JSON.stringify({ company_name: organization })
          : null
      }
    })
  },
  { immediate: true },
)

// A contact picked for another organization would not match the filter.
// Started after the defaults are applied, so a contact passed in with its
// organization (e.g. creating a card from a contact) is kept.
function clearContactWhenOrganizationChanges() {
  watch(
    () => deal.doc.organization,
    (organization, previous) => {
      if (organization !== previous) deal.doc.contact = null
    },
  )
}

async function createDeal() {
  if (deal.doc.website && !deal.doc.website.startsWith('http')) {
    deal.doc.website = 'https://' + deal.doc.website
  }
  if (chooseExistingContact.value) {
    deal.doc['first_name'] = null
    deal.doc['last_name'] = null
    deal.doc['email'] = null
    deal.doc['mobile_no'] = null
  } else deal.doc['contact'] = null

  await triggerOnBeforeCreate?.()

  createResource({
    url: 'crm.fcrm.doctype.crm_deal.crm_deal.create_deal',
    params: { doc: deal.doc },
    auto: true,
    validate() {
      error.value = null
      if (deal.doc.annual_revenue) {
        if (typeof deal.doc.annual_revenue === 'string') {
          deal.doc.annual_revenue = deal.doc.annual_revenue.replace(/,/g, '')
        } else if (isNaN(deal.doc.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (
        deal.doc.mobile_no &&
        isNaN(deal.doc.mobile_no.replace(/[-+() ]/g, ''))
      ) {
        error.value = __('Mobile number should be a number')
        return error.value
      }
      if (deal.doc.email && !deal.doc.email.includes('@')) {
        error.value = __('Invalid email address')
        return error.value
      }
      if (!deal.doc.status) {
        error.value = __('Status is required')
        return error.value
      }
      let missing = emptyRequiredFields(
        stageRequired.value.filter((f) => f.required),
        deal.doc,
      )
      if (missing.length) {
        error.value = __('Fill in: {0}', [
          missing.map((f) => __(f.label)).join(', '),
        ])
        return error.value
      }
      isDealCreating.value = true
    },
    onSuccess(name) {
      capture('deal_created')
      completeStep('create_first_deal')
      isDealCreating.value = false
      show.value = false
      router.push({ name: 'Deal', params: { dealId: name } })
    },
    onError(err) {
      isDealCreating.value = false
      if (!err.messages) {
        error.value = err.message
        return
      }
      error.value = err.messages.join('\n')
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Deal' }
  nextTick(() => (show.value = false))
}

onMounted(async () => {
  deal.doc.no_of_employees = '1-10'
  Object.assign(deal.doc, props.defaults)
  chooseExistingOrganization.value = Boolean(props.defaults.organization)
  chooseExistingContact.value = Boolean(props.defaults.contact)

  if (!deal.doc.deal_owner) {
    deal.doc.deal_owner = getUser().name
  }
  await nextTick()
  clearContactWhenOrganizationChanges()

  await pipelineStore.ensureLoaded()
  if (usePipelines.value) {
    // Opened from a funnel's Kanban column: that funnel and stage
    let pipeline = pipelineStore.getPipeline(deal.doc.pipeline)
      ? deal.doc.pipeline
      : pipelines.value[0].name
    let stageInPipeline = pipelineStore
      .getPipeline(pipeline)
      .stages.some((s) => s.name === deal.doc.status)
    deal.doc.pipeline = pipeline
    if (!stageInPipeline) deal.doc.status = firstStage(pipeline)
    return
  }
  if (!deal.doc.status && dealStatuses.value[0]?.value) {
    deal.doc.status = dealStatuses.value[0].value
  }
})
</script>
