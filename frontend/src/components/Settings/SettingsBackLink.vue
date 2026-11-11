<template>
  <!-- Figma "Voltar" in the "Barra superior" (2345:28842, 2345:29277): 32px,
       16px chevron, 14 Medium Uso/Texto/Secundário, 12px before the title.
       A link (or a plain element with @click) so the top bar title style for
       buttons does not apply. -->
  <component
    :is="to ? 'router-link' : 'a'"
    :to="to || undefined"
    :href="to ? undefined : '#'"
    class="inline-flex h-8 min-w-20 shrink-0 items-center gap-1 rounded-[var(--ct-radius-md)] pl-1 pr-2 text-[14px] font-medium leading-5 text-[color:var(--ct-text-secondary)] hover:bg-[var(--ct-action-neutral)]"
    @click="onClick"
  >
    <span class="lucide-chevron-left size-4" aria-hidden="true" />
    {{ __('Back') }}
  </component>
</template>

<script setup>
const props = defineProps({
  // a route; without it the link only emits `click`
  to: { type: [Object, String], default: null },
})
const emit = defineEmits(['click'])

function onClick(event) {
  if (props.to) return
  event.preventDefault()
  emit('click')
}
</script>
