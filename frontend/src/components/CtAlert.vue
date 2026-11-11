<template>
  <!-- Figma Style Guide "Aviso" (960:402): light background in the message's
       color, icon 20px, text 14px in the same color -->
  <div
    role="alert"
    class="flex items-start gap-2.5 rounded-[var(--ct-radius-md)] py-2.5 pl-3.5 pr-2.5 text-p-base font-medium"
    :class="tone.box"
  >
    <component
      :is="tone.icon"
      class="mt-px size-5 shrink-0"
      aria-hidden="true"
    />
    <div class="min-w-0 flex-1 py-px">
      <slot />
    </div>
    <slot name="action" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import InfoIcon from '~icons/lucide/info'
import TriangleAlertIcon from '~icons/lucide/triangle-alert'
import CircleCheckIcon from '~icons/lucide/circle-check'
import CircleXIcon from '~icons/lucide/circle-x'

const props = defineProps({
  // Figma "Tipo": Informação, Aviso, Sucesso, Erro
  type: {
    type: String,
    default: 'info',
    validator: (v) => ['info', 'warning', 'success', 'error'].includes(v),
  },
})

const TONES = {
  info: {
    icon: InfoIcon,
    box: 'bg-[var(--ct-info-soft)] text-[color:var(--ct-info)]',
  },
  warning: {
    icon: TriangleAlertIcon,
    box: 'bg-[var(--ct-warning-soft)] text-[color:var(--ct-warning)]',
  },
  success: {
    icon: CircleCheckIcon,
    box: 'bg-[var(--ct-success-soft)] text-[color:var(--ct-success)]',
  },
  error: {
    icon: CircleXIcon,
    box: 'bg-[var(--ct-danger-soft)] text-[color:var(--ct-danger)]',
  },
}

const tone = computed(() => TONES[props.type] || TONES.info)
</script>
