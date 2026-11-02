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
    @action="updateStep('view', null)"
  />
  <div
    v-else
    class="w-full self-start overflow-hidden rounded-lg border border-outline-gray-1"
  >
    <div
      class="flex h-10 items-center gap-4 border-b border-outline-gray-1 bg-surface-gray-2 px-4 text-xs font-medium text-ink-gray-6"
    >
      <div class="w-7/12">{{ __('Assignment Rule') }}</div>
      <div class="w-3/12">{{ __('Priority') }}</div>
      <div class="w-2/12">{{ __('Enabled') }}</div>
    </div>
    <div class="overflow-y-auto">
      <template
        v-for="(assignmentRule, i) in assignmentRulesList.data"
        :key="assignmentRule.name"
      >
        <AssignmentRuleListItem :data="assignmentRule" />
        <div
          v-if="assignmentRulesList.data.length !== i + 1"
          class="h-px bg-outline-gray-1"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import LucideGitBranch from '~icons/lucide/git-branch'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import AssignmentRuleListItem from './AssignmentRuleListItem.vue'
import { LoadingIndicator } from 'frappe-ui'
import { inject } from 'vue'

const assignmentRulesList = inject('assignmentRulesList')
const updateStep = inject('updateStep')
</script>
