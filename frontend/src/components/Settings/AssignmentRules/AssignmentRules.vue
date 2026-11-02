<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Assignment Rules')">
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
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import AssignmentRulesList from './AssignmentRulesList.vue'
import { createResource } from 'frappe-ui'
import { inject, provide } from 'vue'

const updateStep = inject('updateStep')

const assignmentRulesListData = createResource({
  url: 'crm.api.assignment_rule.get_assignment_rules_list',
  cache: ['assignmentRules', 'get_assignment_rules_list'],
  auto: true,
})

provide('assignmentRulesList', assignmentRulesListData)

const goToNew = () => {
  updateStep('view', null)
}
</script>
