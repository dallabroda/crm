<template>
  <!-- Figma "Linha" of "Distribuição de cards" (2335:10136): name, funnel, how
       the rule distributes and Active. The priority is set in the rule. -->
  <div
    class="ct-table-row cursor-pointer hover:bg-[var(--ct-bg-soft)]"
    :style="columns"
    @click="updateStep('view', data)"
  >
    <div class="ct-table-name" :title="data.description || ''">
      {{ data.name }}
    </div>
    <div class="truncate">{{ funnelLabel }}</div>
    <div class="truncate">{{ howItDistributes }}</div>
    <div class="flex items-center justify-between gap-2" @click.stop>
      <Switch
        size="md"
        :modelValue="!data.disabled"
        @update:modelValue="onToggle"
      />
      <Dropdown
        align="end"
        :options="dropdownOptions"
        @update:open="(open) => open && (isConfirmingDelete = false)"
      >
        <Button
          icon="lucide-more-horizontal"
          variant="ghost"
          size="sm"
          class="ct-row-menu -my-1.5"
          :aria-label="__('Options')"
        />
      </Dropdown>
    </div>
  </div>
  <Dialog
    v-model:open="duplicateDialog.show"
    :title="__('Duplicate Assignment Rule')"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="duplicateDialog.name"
          :label="__('New Assignment Rule Name')"
          type="text"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          variant="subtle"
          :label="__('Close')"
          @click="duplicateDialog.show = false"
        />
        <Button variant="solid" :label="__('Duplicate')" @click="duplicate()" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, inject, ref } from 'vue'
import { ConfirmDelete } from '../../../utils'
import { usersStore } from '@/stores/users'

const { capture } = useTelemetry()

const assignmentRulesList = inject('assignmentRulesList')
const updateStep = inject('updateStep')

const props = defineProps({
  data: { type: Object, required: true },
  // the table's grid-template-columns (AssignmentRulesList.vue)
  columns: { type: Object, default: () => ({}) },
})

const { getUser } = usersStore()

// the funnel the rule's condition picks ("pipeline equals X"), if any
const funnelLabel = computed(() => {
  let conditions
  try {
    conditions = JSON.parse(props.data.assign_condition_json || '[]')
  } catch {
    conditions = []
  }
  let funnel = conditions
    .flat(Infinity)
    .map((_, i, all) => all.slice(i, i + 3))
    .find(
      ([field, op]) =>
        field === 'pipeline' && ['equals', '=', '=='].includes(op),
    )
  return funnel ? __(funnel[2]) : __('All funnels')
})

// "Rodízio entre Juliana Prado e Carlos Menezes" (Figma); the rule's
// description, when it has one, says it in the company's words
const howItDistributes = computed(() => {
  if (props.data.description) return props.data.description
  let names = (props.data.users || []).map((u) => getUser(u).full_name)
  let people =
    names.length > 1
      ? __('{0} and {1}', [names.slice(0, -1).join(', '), names.at(-1)])
      : names[0] || ''
  if (props.data.rule === 'Load Balancing')
    return __('Load balancing among {0}', [people])
  if (props.data.rule === 'Based on Field')
    return __('By the field {0}', [props.data.field || ''])
  return __('Round robin among {0}', [people])
})

const duplicateDialog = ref({
  show: false,
  name: '',
})

const isConfirmingDelete = ref(false)

const deleteAssignmentRule = () => {
  createResource({
    url: 'frappe.client.delete',
    params: {
      doctype: 'Assignment Rule',
      name: props.data.name,
    },
    onSuccess: () => {
      assignmentRulesList.reload()
      isConfirmingDelete.value = false
      toast.success(__('Assignment rule deleted'))
    },
    auto: true,
  })
}

const dropdownOptions = [
  {
    label: __('Duplicate'),
    onClick: () => {
      duplicateDialog.value = {
        show: true,
        name: props.data.name + ' (Copy)',
      }
    },
    icon: 'lucide-copy',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteAssignmentRule(),
    isConfirmingDelete,
  }),
]

const duplicate = () => {
  createResource({
    url: 'crm.api.assignment_rule.duplicate_assignment_rule',
    params: {
      docname: props.data.name,
      new_name: duplicateDialog.value.name,
    },
    onSuccess: (data) => {
      assignmentRulesList.reload()
      toast.success(__('Assignment rule duplicated'))
      duplicateDialog.value.show = false
      duplicateDialog.value.name = ''
      updateStep('view', data)
    },
    auto: true,
  })
}

const onToggle = () => {
  if (!props.data.users_exists && props.data.disabled) {
    toast.error(__('Cannot enable rule without adding users in it'))
    return
  }
  capture('assignment_rule_toggled', { enabled: Boolean(props.data.disabled) })
  setAssignmentRuleValue('disabled', !props.data.disabled, 'status')
}

const setAssignmentRuleValue = (key, value, fieldName = undefined) => {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Assignment Rule',
      name: props.data.name,
      fieldname: key,
      value: value,
    },
    onSuccess: () => {
      assignmentRulesList.reload()
      toast.success(__('Assignment rule {0} updated', [fieldName || key]))
    },
    auto: true,
  })
}
</script>
