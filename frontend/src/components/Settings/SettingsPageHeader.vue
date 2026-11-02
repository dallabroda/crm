<template>
  <!-- Inside the Settings page: title and actions go to the top bar (Figma
       "Configurações · …"), the description stays at the top of the content. -->
  <template v-if="header">
    <Teleport v-if="header.titleTarget.value" :to="header.titleTarget.value">
      <div class="flex min-w-0 items-center gap-2">
        <slot name="title">
          <h1 class="truncate text-3xl font-semibold text-ink-gray-9">
            {{ title }}
          </h1>
        </slot>
        <slot name="badge" />
      </div>
    </Teleport>
    <Teleport
      v-if="$slots.actions && header.actionsTarget.value"
      :to="header.actionsTarget.value"
    >
      <div class="flex items-center gap-2">
        <slot name="actions" />
      </div>
    </Teleport>
  </template>
  <!-- Outside the page (should not happen): the old inline header -->
  <div v-else class="flex items-start justify-between gap-4">
    <div class="flex items-center gap-2">
      <slot name="title">
        <h2 class="text-2xl-semibold text-ink-gray-8">{{ title }}</h2>
      </slot>
      <slot name="badge" />
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
  <p
    v-if="description || $slots.description"
    class="text-p-base text-ink-gray-6"
  >
    <slot name="description">{{ description }}</slot>
  </p>
</template>

<script setup>
import { inject, onMounted, onBeforeUnmount } from 'vue'

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})

// provided by pages/Settings.vue
const header = inject('settingsHeader', null)

onMounted(() => header && header.count.value++)
onBeforeUnmount(() => header && header.count.value--)
</script>
