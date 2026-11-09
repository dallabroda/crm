<template>
  <!-- Figma "Barra superior": page title 20 Semi Bold. The saved-view switch
       ("Lista ˅") lives on the right, next to "Criar" (ViewSwitcher). -->
  <div class="flex min-w-0 items-center gap-3">
    <router-link
      :to="{ name: routeName }"
      class="truncate rounded-[var(--ct-radius-sm)] text-[20px] font-semibold leading-7 text-ink-gray-9 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
    >
      {{ __(title || routeName) }}
    </router-link>
  </div>
</template>
<script setup>
defineProps({
  routeName: { type: String, required: true },
  // shown instead of the route name (a funnel shows its own name), translated
  // with __() like the sidebar does, so "Sales" reads "Vendas" in both places
  title: { type: String, default: '' },
})
</script>
