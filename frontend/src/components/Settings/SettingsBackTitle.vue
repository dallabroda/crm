<template>
  <!-- Figma "Barra superior" of Funis · Etapas (2339:10530): a ghost "Voltar"
       (gray chevron and label) 12px before the 20 Semi Bold title; "!" wins
       over the 20px title style pages/Settings.vue gives top bar buttons -->
  <button
    type="button"
    class="flex h-8 w-20 shrink-0 items-center gap-1 rounded-[8px] pl-1 pr-2 !text-[14px] !font-medium !leading-5 !text-[var(--ct-text-secondary)] hover:bg-[var(--ct-bg-soft)]"
    @click="emit('back')"
  >
    <span class="lucide-chevron-left size-4" aria-hidden="true" />
    {{ __('Back') }}
  </button>
  <h1
    class="ml-1 truncate text-[20px] font-semibold leading-7 text-[var(--ct-text-primary)]"
  >
    {{ title }}
  </h1>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
})

const emit = defineEmits(['back'])
</script>
