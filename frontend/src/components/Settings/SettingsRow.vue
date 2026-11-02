<template>
  <!-- Figma "Linha de configuração": label and help on the left, control on
       the right, 24px apart -->
  <div class="flex items-center justify-between gap-6">
    <div class="flex min-w-0 flex-1 flex-col gap-1">
      <div class="text-base font-medium leading-5 text-ink-gray-9">
        <slot name="label">{{ label }}</slot>
      </div>
      <div
        v-if="description || $slots.description"
        class="text-base leading-5 text-ink-gray-6"
      >
        <slot name="description">{{ description }}</slot>
      </div>
    </div>
    <div v-if="$slots.default" class="flex shrink-0 items-center gap-2">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>
