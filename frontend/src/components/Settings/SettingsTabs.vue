<template>
  <!-- Figma "Abas" (Configurações · Automação 2335:9863, Funis · Etapas
       2339:10530): 14 Medium tabs, 24px apart, the active one in the accent
       color over a 2px line, on a #dcdde2 bottom border -->
  <div
    class="flex shrink-0 items-start gap-6 border-b border-[var(--ct-border)]"
    role="tablist"
  >
    <button
      v-for="tab in tabs"
      :key="tab.value"
      type="button"
      role="tab"
      :aria-selected="modelValue === tab.value"
      class="flex flex-col"
      @click="emit('update:modelValue', tab.value)"
    >
      <span
        class="px-1 py-2.5 text-[14px] font-medium leading-5"
        :class="
          modelValue === tab.value
            ? 'text-[var(--ct-text-accent)]'
            : 'text-[var(--ct-text-secondary)] hover:text-[var(--ct-text-primary)]'
        "
      >
        {{ tab.label }}
      </span>
      <span
        class="h-0.5 w-full"
        :class="modelValue === tab.value ? 'bg-[var(--ct-text-accent)]' : ''"
      />
    </button>
  </div>
</template>

<script setup>
defineProps({
  // [{ label, value }]
  tabs: { type: Array, required: true },
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
</script>
