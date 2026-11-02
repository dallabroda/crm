<template>
  <div v-if="brand?.logo">
    <img :src="brand.logo" class="h-full w-full object-cover" />
  </div>
  <!-- sized by the caller (the sidebar header uses 28px, radius 7) -->
  <div v-else><CRMLogo class="h-full w-full" /></div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
