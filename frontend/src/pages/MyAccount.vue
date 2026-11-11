<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <!-- a step of the profile (e-mail settings) brings its own title and
             back button: it takes the place of "Minha conta" -->
        <div class="ct-account-title flex min-w-0 items-center gap-3">
          <ViewBreadcrumbs routeName="My Account" title="My account" />
          <div ref="profileTitle" />
        </div>
      </template>
      <template #right-header>
        <div ref="profileActions" class="flex items-center gap-2" />
      </template>
    </LayoutHeader>

    <!-- Figma "Minha conta" (2323:12889): the profile and the preferences on
         one page; 16px top, 24px sides, 32px bottom, 24px between blocks -->
    <div class="ct-account flex-1 overflow-y-auto px-6 pb-8 pt-4">
      <div class="flex flex-col gap-6">
        <AccountSection
          :title-target="profileTitle"
          :actions-target="profileActions"
        >
          <ProfilePage />
        </AccountSection>
        <h2
          class="pt-6 text-[18px] font-semibold leading-6 tracking-[-0.01em] text-ink-gray-9"
        >
          {{ __('Preferences') }}
        </h2>
        <AccountSection :actions-target="profileActions">
          <PreferencesSettings />
        </AccountSection>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import { getSettings } from '@/stores/settings'
import { usePageMeta } from 'frappe-ui'
import { defineComponent, provide, ref, toRef } from 'vue'

const { brand } = getSettings()

const profileTitle = ref(null)
const profileActions = ref(null)

// The settings panels send their title and actions to the top bar the
// Settings page provides (see SettingsPageHeader). Here the panels' own
// titles ("Perfil", "Preferências") are dropped; only a step's title (the
// e-mail settings' back button) and the actions reach the top bar.
const AccountSection = defineComponent({
  props: {
    titleTarget: { type: Object, default: null },
    actionsTarget: { type: Object, default: null },
  },
  setup(props, { slots }) {
    provide('settingsHeader', {
      titleTarget: toRef(props, 'titleTarget'),
      actionsTarget: toRef(props, 'actionsTarget'),
      count: ref(0),
    })
    return () => slots.default?.()
  },
})

usePageMeta(() => ({ title: __('My account'), icon: brand.favicon }))
</script>

<style scoped>
/* a panel's plain title stays out; a step's title (with its back button)
   replaces "Minha conta" */
.ct-account-title :deep(h1) {
  display: none;
}
.ct-account-title:has(button) > :first-child {
  display: none;
}

/* "Idioma e horário" heading row: 24px like the other section titles */
.ct-account :deep(.h-7:has(> .text-lg)) {
  height: 24px;
}

/* the row selects (status, language, time zone) are Figma "Filtro":
   32px, #dcdde2 border, 6px radius, black 14/500 */
.ct-account :deep(.border-outline-gray-2.bg-surface-base) {
  min-height: 32px;
  height: 32px;
  padding-left: 12px;
  border-color: var(--ct-border);
  border-radius: var(--ct-radius-sm);
  color: var(--ct-text-primary);
  font-size: 14px;
  font-weight: 500;
}
</style>
