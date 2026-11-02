<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <!-- the panel's SettingsPageHeader teleports its title here -->
        <div ref="titleTarget" class="settings-title flex min-w-0 items-center">
          <h1
            v-if="!headerCount && activeItem"
            class="truncate text-3xl font-semibold text-ink-gray-9"
          >
            {{ activeItem.title }}
          </h1>
        </div>
      </template>
      <template #right-header>
        <div ref="actionsTarget" class="flex items-center gap-2" />
      </template>
    </LayoutHeader>

    <div class="flex min-h-0 flex-1 gap-12 px-6">
      <!-- Settings menu (Figma "Navegação das configurações") -->
      <nav
        ref="navRef"
        class="flex w-56 shrink-0 flex-col gap-0.5 overflow-y-auto pb-8 pt-4"
        :aria-label="__('Settings')"
      >
        <template v-for="(section, i) in sections" :key="section.key">
          <div
            class="px-2.5 pb-1 text-xs font-medium uppercase tracking-[0.1em] text-ink-gray-4"
            :class="i === 0 ? 'pt-1' : 'pt-3'"
          >
            {{ section.label }}
          </div>
          <router-link
            v-for="item in section.items"
            :key="item.slug"
            :to="{ name: 'Settings', params: { section: item.slug } }"
            :data-page="item.slug"
            class="flex min-h-9 shrink-0 items-center gap-2.5 rounded-lg px-2.5 py-2 text-base leading-5 transition-colors"
            :class="
              item.slug === activeItem?.slug
                ? 'bg-surface-gray-4 font-medium text-ink-gray-9'
                : 'text-ink-gray-6 hover:bg-surface-gray-2'
            "
            :aria-current="item.slug === activeItem?.slug ? 'page' : undefined"
          >
            <Icon :icon="item.icon" class="size-4 shrink-0" />
            <span>{{ item.label }}</span>
          </router-link>
        </template>
      </nav>

      <!-- Active panel -->
      <div class="min-w-0 flex-1 overflow-y-auto pb-8 pt-4">
        <component
          :is="activeItem.component"
          v-if="activeItem"
          :key="activeItem.slug"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Icon from '@/components/Icon.vue'
import {
  getSettingsSections,
  findSettingsItem,
} from '@/components/Settings/settingsSections'
import { plan, loadPlan } from '@/components/Settings/UsersAndPlan/planApi'
import { apiKeys, loadApiKeys } from '@/components/Settings/ApiKeys/apiKeysApi'
import { disableSettingModalOutsideClick } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { usePageMeta } from 'frappe-ui'
import { computed, nextTick, provide, ref, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'

const route = useRoute()
const router = useRouter()
const { isAdmin } = usersStore()

// The plan and the API keys decide whether "Users and Plan", "API" and
// "Cartório & Localização" show up (credtech#25, #175, #290)
if (isAdmin()) {
  loadPlan()
  loadApiKeys()
}

const sections = computed(() => getSettingsSections())

const activeItem = computed(
  () =>
    findSettingsItem(sections.value, route.params.section) ||
    sections.value[0]?.items[0] ||
    null,
)

// An unknown section in the URL (or none) shows the first one; keep the URL
// in step, unless the section is waiting for the plan/API keys to load.
function waitingFor(section) {
  if (section === 'users-and-plan') return plan.loading
  if (['api', 'bureaus'].includes(section)) return apiKeys.loading
  return false
}
watch(
  [
    () => route.params.section,
    sections,
    () => plan.loading,
    () => apiKeys.loading,
  ],
  ([section]) => {
    if (route.name !== 'Settings' || !activeItem.value) return
    if (section === activeItem.value.slug) return
    if (waitingFor(section)) return
    router.replace({
      name: 'Settings',
      params: { section: activeItem.value.slug },
    })
  },
  { immediate: true },
)

// Top bar slots for the panel's SettingsPageHeader
const titleTarget = ref(null)
const actionsTarget = ref(null)
const headerCount = ref(0)
provide('settingsHeader', {
  titleTarget,
  actionsTarget,
  count: headerCount,
})

// Keep the active item in view in the settings menu (deep links)
const navRef = ref(null)
watch(
  () => activeItem.value?.slug,
  (slug) =>
    nextTick(() =>
      navRef.value
        ?.querySelector(`[data-page="${slug}"]`)
        ?.scrollIntoView({ block: 'nearest' }),
    ),
  { immediate: true },
)

// Some editors used to lock the settings modal while they had unsaved
// changes; on a page, ask before leaving the settings.
onBeforeRouteLeave(() => {
  if (!disableSettingModalOutsideClick.value) return true
  if (!window.confirm(__('You have unsaved changes. Do you wish to exit?')))
    return false
  disableSettingModalOutsideClick.value = false
  return true
})

usePageMeta(() => ({
  title: activeItem.value
    ? `${activeItem.value.label} · ${__('Settings')}`
    : __('Settings'),
}))
</script>

<style scoped>
/* Titles teleported by the panels (plain or "back" buttons) use the top bar
   title style: 20px, semibold (Figma "Barra superior"). */
.settings-title :deep(h1),
.settings-title :deep(h2),
.settings-title :deep(button) {
  font-size: 20px;
  line-height: 28px;
  font-weight: 600;
  color: var(--ink-gray-9);
}
</style>
