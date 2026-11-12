<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <!-- Figma "Configurações · Automação · Distribuição de cards" (2335:10136) -->
    <AutomationTabs current="assignment-rules" />
    <SettingsPageHeader :title="__('Automation')">
      <template #description>
        {{
          __(
            'Auto-assign leads/deals to the right sales user based on predefined conditions.',
          )
        }}
      </template>
      <template #actions>
        <Button
          :label="__('New rule')"
          icon-left="lucide-plus"
          variant="solid"
          @click="goToNew()"
        />
      </template>
    </SettingsPageHeader>

    <!-- Assignment rules list -->
    <div class="flex h-full overflow-y-auto">
      <AssignmentRulesList />
    </div>
    <!-- "Nova regra" asks the essentials, then opens the full editor -->
    <NewAssignmentRuleModal v-model="showNewRule" @created="openCreated" />
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import AssignmentRulesList from './AssignmentRulesList.vue'
import AutomationTabs from '@/components/Settings/AutomationTabs.vue'
import NewAssignmentRuleModal from './NewAssignmentRuleModal.vue'
import { createResource } from 'frappe-ui'
import { inject, provide, ref } from 'vue'

const updateStep = inject('updateStep')

const assignmentRulesListData = createResource({
  url: 'crm.api.assignment_rule.get_assignment_rules_list',
  cache: ['assignmentRules', 'get_assignment_rules_list'],
  auto: true,
})

provide('assignmentRulesList', assignmentRulesListData)

const showNewRule = ref(false)

const goToNew = () => {
  showNewRule.value = true
}
provide('openNewRule', goToNew)

function openCreated(rule) {
  assignmentRulesListData.reload()
  updateStep('view', rule)
}
</script>
