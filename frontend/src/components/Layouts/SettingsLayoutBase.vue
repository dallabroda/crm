<template>
  <!-- a page shown as a section of another one (Régua de cobrança inside
       Cartório e cobrança): no title or top bar actions, no own scroll -->
  <div v-if="embedded" class="flex flex-col gap-6 text-ink-gray-8">
    <p v-if="description" class="text-base leading-5 text-ink-gray-6">
      {{ description }}
    </p>
    <slot name="content" />
  </div>
  <div v-else class="flex h-full w-full flex-col gap-6 text-ink-gray-8">
    <!-- above the description, e.g. the Automação tabs -->
    <slot name="header-top" />
    <!-- Title and actions go to the top bar; the description stays here -->
    <SettingsPageHeader :title="title" :description="description">
      <template v-if="$slots.title" #title><slot name="title" /></template>
      <template v-if="$slots.description" #description>
        <slot name="description" />
      </template>
      <template v-if="$slots['header-actions']" #actions>
        <slot name="header-actions" />
      </template>
    </SettingsPageHeader>
    <div v-if="Boolean($slots['header-bottom'])">
      <slot name="header-bottom" />
    </div>
    <div class="min-h-0 flex-1 overflow-y-auto">
      <slot name="content" />
    </div>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  embedded: { type: Boolean, default: false },
})
</script>
