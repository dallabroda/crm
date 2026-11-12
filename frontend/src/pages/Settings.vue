<template>
  <div class="settings-page flex h-full flex-col overflow-hidden">
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

    <div class="flex min-h-0 flex-1 px-6">
      <!-- Figma "Barra lateral secundária · Configurações HubTech" (2081:26431):
           240px full-height column beside the icon rail, white, right border,
           12px sides / 20px top, "Configurações" 16 Semi Bold, groups 12 Medium
           uppercase, 36px items (14 Regular secondary; active 14 Medium on the
           soft background). Inline when the layout has no column for it. -->
      <Teleport to="#app-secondary-sidebar" :disabled="!secondaryTarget">
        <nav
          class="ct-settings-nav flex w-60 shrink-0 flex-col border-r border-[var(--ct-border-soft)] bg-surface-base pt-5"
          :aria-label="__('Settings')"
        >
          <!-- the title stays put; only the list below scrolls -->
          <div class="shrink-0 px-3 pb-3.5">
            <div
              class="pl-2.5 text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Settings') }}
            </div>
          </div>
          <div
            ref="navRef"
            class="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto px-3 pb-5"
          >
            <template v-for="group in nav" :key="group.key">
              <div
                class="pb-0.5 pl-2.5 pt-[11px] text-[12px] font-medium uppercase tracking-[1.2px] text-[var(--ct-text-tertiary)]"
              >
                {{ group.label }}
              </div>
              <template v-for="entry in group.entries" :key="entry.key">
                <router-link
                  :to="{ name: 'Settings', params: { section: entry.target } }"
                  :data-page="entry.target"
                  class="flex min-h-9 shrink-0 items-center gap-2.5 rounded-lg px-2.5 py-2 text-[14px] leading-5 transition-colors"
                  :class="
                    isActiveEntry(entry)
                      ? 'bg-[var(--ct-bg-soft)] font-medium text-[var(--ct-text-primary)]'
                      : 'text-[var(--ct-text-secondary)] hover:bg-[var(--ct-bg-soft)]'
                  "
                  :aria-current="isActiveEntry(entry) ? 'page' : undefined"
                >
                  <Icon :icon="entry.icon" class="size-4 shrink-0" />
                  <span>{{ entry.label }}</span>
                </router-link>
              </template>
            </template>
          </div>
        </nav>
      </Teleport>

      <!-- Active panel (Figma "Conteúdo": 24px sides, 16px top) -->
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
  getSettingsNav,
  findSettingsItem,
} from '@/components/Settings/settingsSections'
import { plan, loadPlan } from '@/components/Settings/UsersAndPlan/planApi'
import { apiKeys, loadApiKeys } from '@/components/Settings/ApiKeys/apiKeysApi'
import { disableSettingModalOutsideClick } from '@/composables/settings'
import {
  SETTINGS_ALIASES,
  settingsRoute,
} from '@/composables/settingsNavigation'
import { usersStore } from '@/stores/users'
import { usePageMeta } from 'frappe-ui'
import { computed, nextTick, onMounted, provide, ref, watch } from 'vue'
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
const nav = computed(() => getSettingsNav(sections.value))

function isActiveEntry(entry) {
  return entry.slugs.includes(activeItem.value?.slug)
}

const activeItem = computed(
  () =>
    findSettingsItem(
      sections.value,
      SETTINGS_ALIASES[route.params.section]?.[0] || route.params.section,
    ) ||
    // the first entry of the sidebar (Perfil moved to "Minha conta")
    findSettingsItem(sections.value, nav.value[0]?.entries[0]?.target) ||
    sections.value[0]?.items[0] ||
    null,
)

// An unknown section in the URL (or none) shows the first one; keep the URL
// in step, unless the section is waiting for the plan/API keys to load.
function waitingFor(section) {
  if (section === 'users-and-plan') return plan.loading
  if (
    ['api', 'bureaus', 'collection-reminders', 'erp-integration'].includes(
      section,
    )
  )
    return apiKeys.loading
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
    // an old section now inside a page (/settings/brand → Empresa #brand)
    if (SETTINGS_ALIASES[section]) {
      router.replace(settingsRoute(section))
      return
    }
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

// the desktop layout has a column for the settings menu; elsewhere it stays
// inline in the page
const secondaryTarget = ref(false)
onMounted(() => {
  secondaryTarget.value = Boolean(
    document.getElementById('app-secondary-sidebar'),
  )
})
</script>

<style scoped>
/* Same Lucide line as the main sidebar (Figma 1.4px at 16px): frappe-ui draws
   them at 1.5 of 24, which reads thinner next to the rail */
.ct-settings-nav :deep(svg) {
  stroke-width: 2.1;
}
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

<style>
/* Figma "Campo" 48px (labels 14/500 gray, value 16px, 14px side padding),
   for the fields the Figma draws at 48px in the settings */
.settings-page .ct-field-48 input:not([type='checkbox']):not([type='radio']),
.settings-page .ct-field-48 button,
.settings-page .ct-field-48 select {
  height: 48px;
  font-size: 16px;
  padding-inline: 14px;
  border-radius: 6px;
}
.settings-page .ct-field-48 textarea {
  font-size: 16px;
  padding: 12px 14px;
  border-radius: 6px;
}
.settings-page .ct-field-48 label {
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  line-height: 20px;
  color: var(--ink-gray-6);
}
/* Figma "Campo com ajuda": the help under the field is 12/16 Texto/Terciário */
.settings-page .ct-field-48 [data-slot='description'] {
  font-size: 12px;
  line-height: 16px;
  color: var(--ct-text-tertiary);
}
</style>
