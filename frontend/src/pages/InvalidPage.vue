<template>
  <div
    class="grid h-full place-items-center px-4 py-20 text-center text-lg text-ink-gray-5"
  >
    <div class="space-y-2">
      <div>{{ __('Invalid page or not permitted to access') }}</div>
      <Button
        :route="{ name: 'Deals' }"
        :label="__('Deals')"
        :iconLeft="DealsIcon"
      />
    </div>
  </div>
</template>

<script setup>
import DealsIcon from '@/components/Icons/DealsIcon.vue'
</script>
