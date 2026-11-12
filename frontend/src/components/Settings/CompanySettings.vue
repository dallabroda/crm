<template>
  <!-- Figma "Configurações · Empresa" (2323:14221): one page with the general
       options first, then "Marca" and "Valores padrão" as sections (18 Semi
       Bold title, actions on its right; 44px above, no divider); "Painel" and "Ações da página
       inicial" follow the same way. The top bar keeps "Empresa". -->
  <div class="flex flex-col">
    <template v-for="(section, i) in visibleSections" :key="section.key">
      <section
        :id="section.key"
        class="flex scroll-mt-4 flex-col gap-5"
        :class="i > 0 ? 'mt-11' : ''"
      >
        <div
          v-if="section.title || i > 0"
          class="flex min-h-8 items-center justify-between gap-4"
        >
          <h2
            v-if="section.title"
            class="text-[18px] font-semibold leading-6 text-ink-gray-9"
          >
            {{ __(section.title) }}
          </h2>
          <div
            :ref="(el) => (actionTargets[section.key] = el)"
            class="ml-auto flex items-center gap-2"
          />
        </div>
        <div
          v-else
          :ref="(el) => (actionTargets[section.key] = el)"
          class="flex justify-end empty:hidden"
        />
        <CompanySection :actions-target="actionTargets[section.key]">
          <component :is="section.component" />
        </CompanySection>
      </section>
    </template>
  </div>
</template>

<script setup>
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
import DefaultsSettings from '@/components/Settings/DefaultsSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import HomeActions from '@/components/Settings/HomeActions.vue'
import { usersStore } from '@/stores/users'
import {
  computed,
  defineComponent,
  markRaw,
  nextTick,
  onMounted,
  provide,
  reactive,
  ref,
  toRef,
} from 'vue'
import { useRoute } from 'vue-router'

const { isManager } = usersStore()
const route = useRoute()

const sections = [
  { key: 'general', title: '', component: markRaw(GeneralSettings) },
  { key: 'brand', title: 'Marca', component: markRaw(BrandSettings) },
  {
    key: 'defaults',
    title: 'Valores padrão',
    component: markRaw(DefaultsSettings),
  },
  { key: 'dashboard', title: 'Painel', component: markRaw(DashboardSettings) },
  {
    key: 'home-actions',
    title: 'Ações da página inicial',
    component: markRaw(HomeActions),
  },
]

// same rule as the old "System Configuration" / "Customization" groups
const visibleSections = computed(() => (isManager() ? sections : []))

const actionTargets = reactive({})

// Each panel's SettingsPageHeader sends its actions next to its section
// title; the panel's own title is not shown (the section title replaces
// it, and the top bar says "Empresa").
const CompanySection = defineComponent({
  props: { actionsTarget: { type: Object, default: null } },
  setup(props, { slots }) {
    provide('settingsHeader', {
      titleTarget: ref(null),
      actionsTarget: toRef(props, 'actionsTarget'),
      count: ref(0),
    })
    return () => slots.default?.()
  },
})

// old links to a section (/settings/brand …) land here with its hash
onMounted(async () => {
  const id = route.hash?.slice(1)
  if (!id) return
  await nextTick()
  document.getElementById(id)?.scrollIntoView({ block: 'start' })
})
</script>
