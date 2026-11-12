<template>
  <div
    v-if="assignmentRulesList.loading && !assignmentRulesList.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <SettingsEmptyState
    v-else-if="assignmentRulesList.data?.length === 0"
    :icon="LucideGitBranch"
    :title="__('No assignment rules yet')"
    :description="
      __('Create rules to share the cards among the team automatically.')
    "
    :action-label="__('New rule')"
    @action="openNewRule"
  />
  <div v-else class="ct-table w-full self-start">
    <div class="ct-table-head" :style="columns">
      <div>{{ __('Name') }}</div>
      <div>{{ __('Funnel') }}</div>
      <div>{{ __('How it distributes') }}</div>
      <div>{{ __('Active', null, 'automation') }}</div>
    </div>
    <AssignmentRuleListItem
      v-for="assignmentRule in assignmentRulesList.data"
      :key="assignmentRule.name"
      :data="assignmentRule"
      :columns="columns"
    />
  </div>
</template>

<script setup>
import LucideGitBranch from '~icons/lucide/git-branch'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import AssignmentRuleListItem from './AssignmentRuleListItem.vue'
import { LoadingIndicator } from 'frappe-ui'
import { inject } from 'vue'
import '@/components/Settings/settingsTable.css'

const assignmentRulesList = inject('assignmentRulesList')
const updateStep = inject('updateStep')
// the short "Nova regra" modal of the page, or the blank editor
const openNewRule = inject('openNewRule', () => updateStep('view', null))

// Figma column widths at 1440px (Nome 305, Funil 152, Como distribui 437,
// Ativa 104), kept in proportion on other widths
const columns = {
  gridTemplateColumns:
    'minmax(0,305fr) minmax(0,152fr) minmax(0,437fr) minmax(0,104fr)',
}
</script>
