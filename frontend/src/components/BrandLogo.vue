<template>
  <!-- Figma "Barra lateral · HubTech" (1038:402) "Logo da empresa": 28px,
       radius 7, sized by the caller. The company's logo (Settings > Brand)
       fits whole inside the square; without one, the HubTech icon. -->
  <div v-if="brand?.logo">
    <img :src="brand.logo" class="h-full w-full object-contain" />
  </div>
  <div v-else>
    <img :src="hubtechIcon" alt="HubTech CRM" class="h-full w-full" />
  </div>
</template>

<script setup>
import hubtechIcon from '@/assets/hubtech-icon.png'

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
