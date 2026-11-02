<template>
  <!-- Figma "Painel · Visão geral · vazia" (838:2): a gray outline of the
       chart behind a white pill with the message -->
  <div class="absolute inset-0 overflow-hidden" aria-hidden="true">
    <div
      v-if="kind === 'donut'"
      class="flex h-full items-center justify-center gap-10"
    >
      <div
        class="size-40 shrink-0 rounded-full border-[24px] border-[var(--ct-action-light-hover)]"
      />
      <div class="flex flex-col gap-8">
        <div v-for="w in [72, 56, 72]" :key="w" class="flex items-center gap-2">
          <div class="size-2 rounded-full bg-[var(--ct-action-light-hover)]" />
          <div
            class="h-2 rounded-full bg-[var(--ct-action-light-hover)]"
            :style="{ width: w + 'px' }"
          />
        </div>
      </div>
    </div>
    <div
      v-else-if="kind === 'rows'"
      class="flex h-full flex-col justify-around py-2 pl-[15%] pr-[5%]"
    >
      <div
        v-for="w in [100, 85, 70, 55, 40, 25]"
        :key="w"
        class="h-5 rounded bg-[var(--ct-action-light-hover)]"
        :style="{ width: w + '%' }"
      />
    </div>
    <div
      v-else
      class="flex h-full items-end justify-around border-b border-[var(--ct-action-light-hover)] px-4"
    >
      <div
        v-for="(h, i) in [55, 80, 40, 95, 45, 75, 35, 70]"
        :key="i"
        class="w-[6%] rounded-t bg-[var(--ct-action-light-hover)]"
        :style="{ height: h + '%' }"
      />
    </div>
  </div>
  <div
    class="relative rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-base px-4 py-2.5 text-base text-ink-gray-6"
  >
    {{ __('No data to show in this chart yet.') }}
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ kind?: 'bars' | 'rows' | 'donut' }>(), {
  kind: 'bars',
})
</script>
