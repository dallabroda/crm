<template>
  <div class="flex h-screen w-screen">
    <AppSidebar />
    <!-- a page's own full-height column ("Barra lateral secundária", e.g. the
         settings menu) teleports here, between the sidebar and the header -->
    <div id="app-secondary-sidebar" class="contents"></div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-base">
      <AppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
import { availabilityStore } from '@/stores/availability'

// listen for status changes from the start, not only once a picker opens
availabilityStore()
</script>
