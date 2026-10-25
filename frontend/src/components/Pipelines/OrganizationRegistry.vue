<template>
  <div
    v-if="organization?.name && rows.length"
    class="border-b px-4 py-3"
    data-testid="organization-registry"
  >
    <div class="mb-2 flex items-center justify-between">
      <div class="text-base-medium text-ink-gray-8">
        {{ __(section.label) }}
      </div>
      <router-link
        class="text-sm text-ink-gray-5 hover:text-ink-gray-8"
        :to="{
          name: 'Organization',
          params: { organizationId: organization.name },
        }"
      >
        {{ __('Edit in the organization') }}
      </router-link>
    </div>
    <div class="flex flex-col gap-1.5">
      <div
        v-for="row in rows"
        :key="row.fieldname"
        class="flex gap-2 text-base"
        :data-registry-field="row.fieldname"
      >
        <div class="w-2/5 shrink-0 truncate text-ink-gray-5">
          {{ __(row.label) }}
        </div>
        <div class="truncate text-ink-gray-8">{{ row.value }}</div>
      </div>
    </div>
  </div>
</template>
<script setup>
// The company registry data (CNPJ, Receita) lives only on the Organization
// (credtech#34: no copies on the card). The card shows it read-only, using the
// fields and order of the Organization side panel section the cred_hub app
// sets up; without that section nothing is shown.
import { formatDate } from '@/utils'
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

const SECTION = 'cred_hub_cnpj_section'

const props = defineProps({
  // the card's Organization document (doc of useDocument)
  organization: { type: Object, default: null },
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  params: { doctype: 'CRM Organization' },
  cache: ['sidepanel-sections', 'CRM Organization'],
  auto: true,
})

const section = computed(
  () => (sections.data || []).find((s) => s.name === SECTION) || {},
)

function display(field, value) {
  if (value === null || value === undefined || value === '') return ''
  if (field.fieldtype === 'Date') return formatDate(value, '', true)
  if (field.fieldtype === 'Check') return value ? __('Yes') : __('No')
  if (['Currency', 'Float'].includes(field.fieldtype)) {
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
  }
  return field.fieldtype === 'Select' ? __(value) : String(value)
}

const rows = computed(() => {
  let fields = (section.value.columns || []).flatMap((c) => c.fields || [])
  return fields
    .filter((f) => f && typeof f === 'object')
    .map((f) => ({
      fieldname: f.fieldname,
      label: f.label,
      value: display(f, props.organization?.[f.fieldname]),
    }))
    .filter((r) => r.value)
})
</script>
