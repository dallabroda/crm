<template>
  <!-- Figma "Barra superior": white, bottom border #e6e7eb, 24px right edge -->
  <div
    class="flex border-b border-[var(--ct-border-soft)] bg-surface-base pr-6"
  >
    <div id="app-header" class="flex-1"></div>
    <div class="flex items-center justify-center">
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
</script>
