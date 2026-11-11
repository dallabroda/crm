<template>
  <!-- Figma "Configurações · Automação" (2335:9863, 2335:10136, 2335:10382):
       the automations, card distribution and SLA panels read as one page with
       three tabs; each tab opens its settings section -->
  <SettingsTabs :tabs="tabs" :model-value="current" @update:model-value="go" />
</template>

<script setup>
import SettingsTabs from './SettingsTabs.vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // slug of the section showing the tabs
  current: { type: String, required: true },
})

const router = useRouter()

// same condition as the Workflow Automations section (settingsSections.js)
const tabs = [
  ...(window.has_automation_engine
    ? [{ label: __('Automations'), value: 'workflow-automations' }]
    : []),
  { label: __('Card distribution'), value: 'assignment-rules' },
  { label: __('Deadlines (SLA)'), value: 'sla-policies' },
]

function go(section) {
  if (section === props.current) return
  router.push({ name: 'Settings', params: { section } })
}
</script>
