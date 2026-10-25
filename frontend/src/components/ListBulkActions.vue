<template>
  <EditValueModal
    v-if="showEditModal"
    v-model="showEditModal"
    :doctype="doctype"
    :selectedValues="selectedValues"
    @reload="reload"
  />
  <AssignmentModal
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="bulkAssignees"
    :docs="selectedValues"
    :doctype="doctype"
    @reload="reload"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteDocModal.showLinkedDocsModal"
    v-model="showDeleteDocModal.showLinkedDocsModal"
    :doctype="props.doctype"
    :docname="showDeleteDocModal.docname"
    :reload="reload"
  />
  <BulkDeleteLinkedDocModal
    v-if="showDeleteDocModal.showDeleteModal"
    v-model="showDeleteDocModal.showDeleteModal"
    :doctype="props.doctype"
    :items="showDeleteDocModal.items"
    :reload="reload"
  />
  <Dialog v-model:open="bulkConvert.open" :size="'md'">
    <template #title>
      <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
        {{ __('Convert to Deal') }}
      </h3>
    </template>
    <template #default>
      <p class="mb-4 text-p-base text-ink-gray-7">
        {{
          __('Are you sure you want to convert {0} lead(s) to deal(s)?', [
            bulkConvert.names.length,
          ])
        }}
      </p>
      <PipelineSelect
        v-model="bulkConvert.pipeline"
        :description="__('The card starts in the first stage of this funnel.')"
      />
      <ErrorMessage class="mt-4" :message="bulkConvert.error" />
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="__('Convert')"
          variant="solid"
          :loading="bulkConvert.loading"
          @click="submitBulkConvert"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditValueModal from '@/components/Modals/EditValueModal.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import PipelineSelect from '@/components/Pipelines/PipelineSelect.vue'
import { setupListCustomizations } from '@/utils'
import { globalStore } from '@/stores/global'
import { useTelemetry } from '@framework/ui/telemetry'
import { Button, Dialog, ErrorMessage, call, toast } from 'frappe-ui'
import { createToast, scriptToast } from '@/utils/scriptToast'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  options: {
    type: Object,
    default: () => ({
      hideEdit: false,
      hideDelete: false,
      hideAssign: false,
    }),
  },
})

const list = defineModel({ type: Object })

const router = useRouter()

const { $dialog, $socket } = globalStore()
const { capture } = useTelemetry()

const showEditModal = ref(false)
const selectedValues = ref([])
const unselectAllAction = ref(() => {})
const showDeleteDocModal = ref({
  showLinkedDocsModal: false,
  showDeleteModal: false,
  docname: null,
})
function editValues(selections, unselectAll) {
  selectedValues.value = selections
  showEditModal.value = true
  unselectAllAction.value = unselectAll
}

// every card belongs to a funnel (no default funnel): ask for it once for
// the whole selection
const bulkConvert = ref({
  open: false,
  names: [],
  pipeline: '',
  error: '',
  loading: false,
  unselectAll: null,
})

function convertToDeal(selections, unselectAll) {
  bulkConvert.value = {
    open: true,
    names: Array.from(selections),
    pipeline: '',
    error: '',
    loading: false,
    unselectAll,
  }
}

async function submitBulkConvert() {
  const state = bulkConvert.value
  if (!state.pipeline) {
    state.error = __('Choose the funnel of the cards.')
    return
  }
  state.error = ''
  state.loading = true
  capture('bulk_convert_to_deal')
  // one at a time: each conversion locks its lead and may create contacts
  let failed = 0
  for (const name of state.names) {
    try {
      await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
        lead: name,
        deal: { pipeline: state.pipeline },
      })
    } catch {
      failed++
    }
  }
  state.loading = false
  if (failed) {
    toast.error(
      __('{0} of {1} leads could not be converted', [
        failed,
        state.names.length,
      ]),
    )
  } else {
    toast.success(__('Converted Successfully'))
  }
  list.value.reload()
  state.unselectAll?.()
  state.open = false
}

function deleteValues(selections, unselectAll) {
  unselectAllAction.value = unselectAll

  const selectedDocs = Array.from(selections)
  if (selectedDocs.length == 1) {
    showDeleteDocModal.value = {
      showLinkedDocsModal: true,
      docname: selectedDocs[0],
    }
  } else {
    showDeleteDocModal.value = {
      showDeleteModal: true,
      items: selectedDocs,
    }
  }
}

const showAssignmentModal = ref(false)
const bulkAssignees = ref([])

function assignValues(selections, unselectAll) {
  showAssignmentModal.value = true
  selectedValues.value = selections
  unselectAllAction.value = unselectAll
}

function clearAssignments(selections, unselectAll) {
  $dialog({
    title: __('Clear Assignment'),
    message: __('Are you sure you want to clear assignment for {0} item(s)?', [
      selections.size,
    ]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Clear Assignment'),
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }) => {
          capture('bulk_clear_assignment')
          call('frappe.desk.form.assign_to.remove_multiple', {
            doctype: props.doctype,
            names: JSON.stringify(Array.from(selections)),
            ignore_permissions: true,
          }).then(() => {
            toast.success(__('Assignment Cleared Successfully'))
            reload(unselectAll)
            close()
          })
        },
      },
    ],
  })
}

const customBulkActions = ref([])
const customListActions = ref([])

function bulkActions(selections, unselectAll) {
  let actions = []

  if (!props.options.hideEdit) {
    actions.push({
      label: __('Edit'),
      onClick: () => editValues(selections, unselectAll),
    })
  }

  if (!props.options.hideDelete) {
    actions.push({
      label: __('Delete'),
      onClick: () => deleteValues(selections, unselectAll),
    })
  }

  if (!props.options.hideAssign) {
    actions.push({
      label: __('Assign To'),
      onClick: () => assignValues(selections, unselectAll),
    })
    actions.push({
      label: __('Clear Assignment'),
      onClick: () => clearAssignments(selections, unselectAll),
    })
  }

  if (props.doctype === 'CRM Lead') {
    actions.push({
      label: __('Convert to Deal'),
      onClick: () => convertToDeal(selections, unselectAll),
    })
  }

  customBulkActions.value.forEach((action) => {
    actions.push({
      label: __(action.label),
      onClick: () =>
        action.onClick({
          list: list.value,
          selections,
          unselectAll,
          call,
          createToast,
          toast: scriptToast,
          $dialog,
          router,
        }),
    })
  })
  return actions
}

function reload(unselectAll) {
  showDeleteDocModal.value = {
    showLinkedDocsModal: false,
    showDeleteModal: false,
    docname: null,
  }

  unselectAllAction.value?.()
  unselectAll?.()
  list.value?.reload()
}

onMounted(async () => {
  if (!list.value?.data) return
  let customization = await setupListCustomizations(list.value.data, {
    list: list.value,
    call,
    $dialog,
    $socket,
    router,
  })
  customBulkActions.value =
    customization?.bulkActions || list.value?.data?.bulkActions || []
  customListActions.value =
    customization?.actions || list.value?.data?.listActions || []
})

defineExpose({
  bulkActions,
  customListActions,
})
</script>
