<template>
  <!-- Figma "Divisor": 1px line in a 20px band -->
  <div class="flex h-5 items-center" role="separator">
    <!-- a border, not bg-outline-*: Tailwind only builds outline colors
         as border utilities -->
    <div class="w-full border-t border-outline-gray-2" />
  </div>
</template>
