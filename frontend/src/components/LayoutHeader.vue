<template>
  <Teleport v-if="showHeader" to="#app-header">
    <slot>
      <!-- Figma "Barra superior" (960:198): 64px, 24px sides, title on the
           left, actions on the right with 8px gaps. -->
      <header
        class="flex h-12 items-center justify-between gap-2 pl-2 sm:h-16 sm:pl-6"
      >
        <div class="flex min-w-0 items-center gap-3">
          <slot name="left-header" />
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
