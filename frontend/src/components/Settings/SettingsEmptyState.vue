<template>
  <!-- Figma "Estado vazio": icon, title, help and the main action -->
  <div class="flex w-full justify-center px-6 py-4">
    <div
      class="flex max-w-md flex-col items-center gap-3 px-6 py-8 text-center"
    >
      <Icon v-if="icon" :icon="icon" class="size-7.5 text-ink-gray-9" />
      <div class="flex flex-col items-center gap-1">
        <span class="text-lg font-medium leading-6 text-ink-gray-9">
          {{ title }}
        </span>
        <span v-if="description" class="text-base leading-5 text-ink-gray-6">
          {{ description }}
        </span>
      </div>
      <div v-if="actionLabel || $slots.actions" class="flex items-center gap-2">
        <slot name="actions">
          <Button
            variant="solid"
            icon-left="lucide-plus"
            :label="actionLabel"
            @click="emit('action')"
          />
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'

defineProps({
  icon: { type: [String, Object, Function], default: null },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
})

const emit = defineEmits(['action'])
</script>
