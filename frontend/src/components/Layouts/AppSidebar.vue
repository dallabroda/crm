<template>
  <!-- The notifications panel is absolutely positioned at `left: 100%`, so it
       needs a positioning context that is not the Sidebar itself (Sidebar sets
       overflow-x-hidden, which would clip the panel away).

       It also paints the sidebar surface: Sidebar's own `bg-surface-sidebar` is
       transparent in dark mode, and nothing behind it sets a background, so the
       column falls through to the white page canvas. -->
  <div class="relative flex h-full bg-surface-base">
    <!-- Figma "Barra lateral · HubTech" (1073:13444): 256px expanded,
         72px icon rail when collapsed. -->
    <Sidebar
      v-model:collapsed="isSidebarCollapsed"
      :collapsible="!mobile"
      :width="mobile ? '260px' : '256px'"
      collapsedWidth="72px"
      class="ct-sidebar border-r border-[var(--ct-border-soft)] !bg-surface-base"
    >
      <div
        class="flex h-full flex-col pb-2 transition-[padding] duration-300 ease-in-out"
        :class="isCollapsed ? 'px-[18px]' : 'px-3'"
      >
        <!-- Header: company logo + name, collapse button -->
        <div
          class="flex shrink-0 items-center gap-2.5 border-b border-surface-gray-3"
          :class="
            isCollapsed
              ? 'justify-center border-b-0 pt-[11px]'
              : 'h-[47px] pl-1.5'
          "
        >
          <BrandLogo
            v-model="brand"
            class="size-7 shrink-0 overflow-hidden rounded-[7px]"
          />
          <span
            v-if="!isCollapsed"
            class="min-w-0 flex-1 truncate text-[14px] font-medium leading-5 tracking-normal text-ink-gray-9"
          >
            {{ brand.name || 'HubTech CRM' }}
          </span>
          <button
            v-if="!mobile && !isCollapsed"
            type="button"
            class="ct-sidebar-toggle"
            :aria-label="__('Collapse')"
            @click="isSidebarCollapsed = true"
          >
            <ChevronLeftIcon class="size-4" />
          </button>
        </div>

        <!-- Search opens the command palette; collapsed, the slot holds the expand button -->
        <!-- Figma "Busca": 4px below the header, 12px above and 4px below the
             32px field. Collapsed: the expand button, 16px under the logo. -->
        <div
          class="flex shrink-0 items-center justify-center"
          :class="isCollapsed ? 'pt-4' : 'mt-1 h-12 pb-1 pt-3'"
        >
          <Tooltip v-if="isCollapsed" :text="__('Expand')" side="right">
            <button
              type="button"
              class="ct-sidebar-toggle"
              :aria-label="__('Expand')"
              @click="isSidebarCollapsed = false"
            >
              <ChevronRightIcon class="size-4" />
            </button>
          </Tooltip>
          <button
            v-else
            type="button"
            class="ct-sidebar-icons flex h-8 w-full items-center gap-2 rounded-[var(--ct-radius-md)] bg-[var(--ct-bg-soft)] px-2.5 text-left text-[14px] font-normal leading-5 tracking-normal text-ink-gray-4 transition-colors hover:bg-[var(--ct-action-light-hover)]"
            @click="openCommandPalette()"
          >
            <SearchIcon class="size-4 shrink-0" />
            <span class="truncate">{{ __('Search...') }}</span>
          </button>
        </div>

        <!-- overflow-y-auto forces overflow-x to clip too; widen the scroll box
             to the sidebar edges and pad the content back in. -->
        <div
          class="flex flex-1 flex-col gap-1 overflow-y-auto pt-1"
          :class="isCollapsed ? '-mx-[18px] px-[18px]' : '-mx-3 px-3'"
        >
          <CollapsibleSection
            v-for="(section, index) in allViews"
            :key="section.name"
            :label="section.name"
            :opened="section.opened"
          >
            <template #header="{ opened, toggle }">
              <div class="group relative">
                <!-- collapsed rail: a short line separates the groups, 17px under
                     the last icon box and 20px above the next (40px under the
                     expand button for the first one) -->
                <div
                  v-if="isCollapsed"
                  class="flex h-[30px] items-start justify-center pt-[13px]"
                  :class="{ 'mt-[23px]': index === 0 }"
                  aria-hidden="true"
                >
                  <span class="h-px w-7 bg-surface-gray-3" />
                </div>
                <button
                  v-else
                  type="button"
                  class="flex h-[34px] w-full select-none items-end gap-1 pb-1 pl-2.5 pt-3 text-left"
                  :aria-expanded="opened"
                  @click="toggle()"
                >
                  <span
                    class="truncate text-xs font-medium uppercase leading-[18px] tracking-[0.1em] text-ink-gray-4"
                  >
                    {{ __(section.label || section.name) }}
                  </span>
                  <span
                    class="lucide-chevron-down mb-px size-3.5 shrink-0 text-ink-gray-4 opacity-0 transition duration-200 group-hover:opacity-100"
                    :class="{ '-rotate-90 opacity-100': !opened }"
                    aria-hidden="true"
                  />
                </button>
                <!-- Admins and Pipeline Owners: one click opens the editor of a new funnel -->
                <Tooltip
                  v-if="section.name === 'Deals' && showNewPipeline"
                  :text="__('New funnel')"
                  side="right"
                >
                  <button
                    type="button"
                    class="absolute bottom-0.5 right-1 grid size-6 place-items-center rounded-[var(--ct-radius-sm)] text-ink-gray-6 hover:bg-[var(--ct-bg-soft)] hover:text-ink-gray-9"
                    :aria-label="__('New funnel')"
                    @click="openNewPipeline"
                  >
                    <span class="lucide-plus size-4" aria-hidden="true" />
                  </button>
                </Tooltip>
              </div>
            </template>
            <nav class="ct-sidebar-icons flex flex-col gap-1 pt-1">
              <template v-for="link in section.views" :key="link.key">
                <SidebarItem
                  v-if="link.key === 'Notifications'"
                  id="notifications-btn"
                  :class="itemClass"
                  :label="__('Notifications')"
                  :route="mobile ? { name: 'Notifications' } : undefined"
                  :active="mobile && activeItem === 'Notifications'"
                  @click="onNotificationsClick"
                >
                  <template #prefix>
                    <span class="relative grid size-4 place-items-center">
                      <BellIcon class="size-4" />
                      <span
                        v-if="isCollapsed && unreadNotificationsCount"
                        class="absolute -right-[3px] -top-[3px] size-2 rounded-full bg-[var(--ct-counter-alert)]"
                      />
                    </span>
                  </template>
                  <!-- Not in #suffix: that slot sits outside the button, so a
                       click on the count would not toggle the panel. -->
                  <span class="ct-sidebar-label ml-0.5 flex-1 truncate">
                    {{ __('Notifications') }}
                  </span>
                  <span
                    v-if="unreadNotificationsCount"
                    class="mr-2.5 grid h-5 min-w-5 place-items-center rounded-full bg-[var(--ct-counter-alert)] px-1.5 text-xs font-semibold text-white"
                  >
                    {{ unreadNotificationsCount }}
                  </span>
                </SidebarItem>
                <!-- Figma "Ajuda › Suporte": opens the CredTech support on
                     WhatsApp, like Cred Chat's "Suporte" -->
                <SidebarItem
                  v-else-if="link.onClick"
                  :class="itemClass"
                  :label="__(link.label)"
                  @click="link.onClick()"
                >
                  <template #prefix>
                    <Icon :icon="link.icon" class="size-4" />
                  </template>
                  <span class="ct-sidebar-label ml-0.5 truncate">{{
                    __(link.label)
                  }}</span>
                </SidebarItem>
                <SidebarItem
                  v-else
                  :class="itemClass"
                  :route="link.to"
                  :label="__(link.label)"
                  :active="activeItem === link.key"
                  @click="selectItem($event, link.key)"
                >
                  <template #prefix>
                    <Icon :icon="link.icon" class="size-4" />
                  </template>
                  <Tooltip
                    :text="__(link.label)"
                    side="right"
                    :hoverDelay="1500"
                    :disabled="isCollapsed"
                  >
                    <span class="ct-sidebar-label ml-0.5 truncate">{{
                      __(link.label)
                    }}</span>
                  </Tooltip>
                </SidebarItem>
              </template>
            </nav>
          </CollapsibleSection>
        </div>

        <div class="mt-auto flex shrink-0 flex-col gap-1 pt-2">
          <div v-if="!mobile" class="mb-1 flex flex-col gap-2">
            <SignupBanner
              v-if="isDemoSite"
              :isSidebarCollapsed="isCollapsed"
              :afterSignup="() => capture('signup_from_demo_site')"
            />
            <TrialBanner
              v-if="isFCSite"
              :isSidebarCollapsed="isCollapsed"
              :afterUpgrade="() => capture('upgrade_plan_from_trial_banner')"
            />
            <GettingStartedBanner
              v-if="!isOnboardingStepsCompleted"
              :isSidebarCollapsed="isCollapsed"
            />
          </div>
          <SidebarItem
            v-if="!mobile && isManager() && isDemoDataCreated"
            :label="__('Clear Demo Data')"
            :class="itemClass"
            class="!text-ink-red-5 hover:!bg-surface-red-2"
            @click="() => clearDemoData()"
          >
            <template #prefix>
              <BrushCleaningIcon class="size-4" />
            </template>
          </SidebarItem>
          <!-- Footer: the signed-in user opens the account menu -->
          <!-- Figma: 32px avatar 16px above the bottom edge; text 12px
               under the divider -->
          <div
            class="border-t pt-2"
            :class="
              isCollapsed ? 'border-transparent pb-2' : 'border-surface-gray-3'
            "
          >
            <UserDropdown :isCollapsed="isCollapsed" />
          </div>
        </div>
      </div>
    </Sidebar>
    <Notifications v-if="!mobile" />
  </div>

  <template v-if="!mobile">
    <HelpModal
      v-if="showHelpModal"
      v-model="showHelpModal"
      v-model:articles="articles"
      :logo="CRMLogo"
      :afterSkip="(step) => capture('onboarding_step_skipped_' + step)"
      :afterSkipAll="() => capture('onboarding_steps_skipped')"
      :afterReset="(step) => capture('onboarding_step_reset_' + step)"
      :afterResetAll="() => capture('onboarding_steps_reset')"
      title="HubTech CRM"
      docsLink="https://credtechdigital.com.br"
    />
    <IntermediateStepModal
      v-model="showIntermediateModal"
      :currentStep="currentStep"
    />
  </template>
</template>

<script setup>
import BrushCleaningIcon from '~icons/lucide/brush-cleaning'
import BellIcon from '~icons/lucide/bell'
import BuildingIcon from '~icons/lucide/building'
import ChevronLeftIcon from '~icons/lucide/chevron-left'
import ChevronRightIcon from '~icons/lucide/chevron-right'
import CircleCheckIcon from '~icons/lucide/circle-check'
import ContactIcon from '~icons/lucide/contact'
import FileTextIcon from '~icons/lucide/file-text'
import HandshakeIcon from '~icons/lucide/handshake'
import HeadsetIcon from '~icons/lucide/headset'
import LayoutDashboardIcon from '~icons/lucide/layout-dashboard'
import PhoneLucideIcon from '~icons/lucide/phone'
import ReceiptIcon from '~icons/lucide/receipt'
import SearchIcon from '~icons/lucide/search'
import SettingsIcon from '~icons/lucide/settings'
import BrandLogo from '@/components/BrandLogo.vue'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import InviteIcon from '@/components/Icons/InviteIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Icon from '@/components/Icon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import { getNavigationItems } from '@/utils/navigation'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import Notifications from '@/components/Notifications.vue'
import { viewsStore } from '@/stores/views'
import { pipelinesStore } from '@/stores/pipelines'
import { storeToRefs } from 'pinia'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import {
  showSettings,
  activeSettingsPage,
  mobileSidebarOpened,
  newPipelineRequested,
} from '@/composables/settings'
import { useBroadcast } from '@/composables/useBroadcast.js'
import { openCommandPalette } from '@/composables/useCommandPalette'
import { getSettings } from '@/stores/settings'
import { call, Sidebar, SidebarItem, Tooltip } from 'frappe-ui'
import { SignupBanner } from '@framework/ui/components/SignupBanner'
import { TrialBanner } from '@framework/ui/components/TrialBanner'
import {
  HelpModal,
  GettingStartedBanner,
  useOnboarding,
  showHelpModal,
  minimize,
  IntermediateStepModal,
} from '@framework/ui/components/Onboarding'
import { useTelemetry } from '@framework/ui/telemetry'
import router from '@/router'
import { useStorage } from '@vueuse/core'
import { useDemoData } from '@/composables/demoData'
import { useCrmOnboarding } from '@/composables/onboarding'
import { ref, reactive, computed, markRaw, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  mobile: { type: Boolean, default: false },
})

const route = useRoute()

const { getPinnedViews, getPublicViews } = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()
const { capture } = useTelemetry()
const { clearDemoData, isDemoDataCreated } = useDemoData()
const { send } = useBroadcast()

// Figma: every HubTech screen opens with the icon rail (collapsed sidebar);
// a new key so the old stored "expanded" default does not override it.
const storedCollapsed = useStorage('ct-sidebar-collapsed', true)

// Figma "Configurações": the settings pages open with the icon rail (their own
// "Barra lateral secundária" sits beside it). Expanding it there lasts until
// the person leaves the settings; the stored choice is left alone.
const onSettings = computed(() => route.name === 'Settings')
const expandedOnSettings = ref(false)
watch(onSettings, (value) => {
  if (value) expandedOnSettings.value = false
})
const isSidebarCollapsed = computed({
  get: () =>
    onSettings.value ? !expandedOnSettings.value : storedCollapsed.value,
  set: (value) => {
    if (onSettings.value) expandedOnSettings.value = !value
    else storedCollapsed.value = value
  },
})

// The mobile drawer pins the sidebar open, so it is never visually collapsed
// even when the stored rail state says otherwise.
const isCollapsed = computed(() => isSidebarCollapsed.value && !props.mobile)

const { brand } = getSettings()

// Figma "Item da barra lateral": 36px row, 10px inner padding, text Inter 14
// Regular, hover and active on #f5f5f7, active text #2a2b30 Medium. Icons
// follow the text color; on the collapsed rail they are #8e8e93 and the
// active one black, as in "Barra lateral · HubTech" (1073:13444).
const ITEM_BASE =
  '!h-9 font-normal hover:!bg-[var(--ct-bg-soft)] data-[state=active]:!bg-[var(--ct-bg-soft)] data-[state=active]:font-medium [&>a]:!pl-2.5 [&>button]:!pl-2.5'
const itemClass = computed(() =>
  isCollapsed.value
    ? `${ITEM_BASE} text-[#8e8e93] data-[state=active]:!text-ink-gray-9`
    : `${ITEM_BASE} text-ink-gray-6 data-[state=active]:!text-ink-gray-7`,
)

// Figma uses Lucide line icons in the menu; the routes keep their own icons
// everywhere else (command palette, mobile tabs).
const ROUTE_ICONS = {
  Dashboard: LayoutDashboardIcon,
  Contacts: ContactIcon,
  Organizations: BuildingIcon,
  Notes: FileTextIcon,
  Tasks: CircleCheckIcon,
  'Call Logs': PhoneLucideIcon,
}

const isFCSite = ref(window.is_fc_site)
const isDemoSite = ref(window.is_demo_site)

// Figma sidebar (2326:41374): Registros = Contatos, Organizações, Tarefas,
// Ligações. Notes stays reachable from the card and the command palette.
const links = getNavigationItems({ mobile: props.mobile }).filter(
  (link) => link.route !== 'Notes',
)

const pipelineStore = pipelinesStore()
const { pipelines, canCreate: canCreatePipeline } = storeToRefs(pipelineStore)
pipelineStore.ensureLoaded()
pipelineStore.loadCanCreate()

// Settings (where the funnel editor lives) is not available on mobile
const showNewPipeline = computed(
  () => canCreatePipeline.value && !props.mobile && !isCollapsed.value,
)

function openNewPipeline() {
  newPipelineRequested.value = true
  activeSettingsPage.value = __('Funnels')
  showSettings.value = true
}

// Same CredTech support line as Cred Chat's "Suporte", with who is asking
const SUPPORT_WHATSAPP_NUMBER = '554888692538'

function openSupport() {
  const me = getUser() || {}
  const text = __(
    'Hi! I am {0} ({1}) from {2} and I need help with HubTech CRM.',
    [me.full_name || '', me.email || user || '', brand.name || ''],
  )
  window.open(
    `https://wa.me/${SUPPORT_WHATSAPP_NUMBER}?text=${encodeURIComponent(text)}`,
    '_blank',
    'noopener',
  )
}

function navLink(link) {
  return {
    label: link.label,
    icon: ROUTE_ICONS[link.route] || link.icon,
    key: link.route,
    to: { name: link.route },
  }
}

// "Negócios" lists the funnels the user can see; each one opens its Kanban (#72).
// The plain "Deals" entry stays in the command palette, not in the sidebar.
const pipelineViews = computed(() =>
  pipelines.value.map((pipeline) => ({
    label: pipeline.pipeline_name,
    icon: /cobran|collection/i.test(pipeline.pipeline_name || '')
      ? ReceiptIcon
      : HandshakeIcon,
    key: pipelineKey(pipeline.name),
    to: {
      name: 'Deals',
      params: { viewType: 'kanban' },
      query: { pipeline: pipeline.name },
    },
  })),
)

const allViews = computed(() => {
  let top = links.filter((link) => link.route === 'Dashboard')
  let rest = links.filter(
    (link) => !['Dashboard', 'Deals'].includes(link.route),
  )
  let _views = [
    {
      name: 'General',
      opened: true,
      // Início (the dashboard) first, Notificações below it, as in the Figma
      views: [
        ...top.map(navLink),
        { label: 'Notifications', key: 'Notifications' },
      ],
    },
    {
      name: 'Deals',
      // the cards live inside funnels: the header says so and the funnels are indented under it
      label: 'Funnels',
      opened: true,
      views: pipelineViews.value,
      // with no funnel yet, keep the header so the "+" can create the first one
      keep: showNewPipeline.value,
    },
    {
      name: 'All Views',
      label: 'Records',
      opened: true,
      views: rest.map(navLink),
    },
  ].filter((section) => section.views.length || section.keep)
  if (getPublicViews().length) {
    _views.push({
      name: 'Public Views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }

  if (getPinnedViews().length) {
    _views.push({
      name: 'Pinned Views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  // Figma "Ajuda": Settings and Support close the list (no Settings on mobile)
  if (!props.mobile) {
    _views.push({
      name: 'Help',
      opened: true,
      views: [
        {
          label: 'Settings',
          icon: markRaw(SettingsIcon),
          key: 'Settings',
          to: { name: 'Settings' },
        },
        {
          label: 'Support',
          icon: markRaw(HeadsetIcon),
          key: 'Support',
          onClick: openSupport,
        },
      ],
    })
  }
  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      key: view.name,
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return icon

  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

function pipelineKey(name) {
  return 'pipeline:' + name
}

// A saved view's key is its name; a funnel's key is pipeline:<name>; a plain
// nav item's key is its route name.
function currentRouteKey() {
  if (route.query.view) return route.query.view
  if (route.name === 'Deals' && route.query.pipeline) {
    return pipelineKey(route.query.pipeline)
  }
  return route.name
}

// Set the highlight on click rather than waiting for the route, since route
// components are lazily imported and the first visit waits on a chunk fetch.
// Modified clicks open a new tab without navigating this one, so they must not
// move the highlight here.
const activeItem = ref(currentRouteKey())

function selectItem(event, key) {
  if (
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey ||
    event.button === 1
  ) {
    return
  }
  activeItem.value = key
  // Selecting the row for the route already open leaves the URL unchanged, so
  // the drawer's navigation watcher never fires. Close it here too.
  if (props.mobile) {
    mobileSidebarOpened.value = false
  }
}

watch(
  () => [route.name, route.query.view, route.query.pipeline],
  () => (activeItem.value = currentRouteKey()),
)

function onNotificationsClick(event) {
  if (props.mobile) {
    selectItem(event, 'Notifications')
  } else {
    toggleNotificationPanel()
  }
}

// onboarding
const { user } = sessionStore()
const { users, isManager, getUser } = usersStore()
const { isOnboardingStepsCompleted, setUp } = useOnboarding('frappecrm')
const { flushPendingSteps } = useCrmOnboarding()

// The onboarding composable persists the checklist as a positional
// [{name, completed}] list, seeds it from the current steps ONLY when empty,
// and never adds newly introduced steps to an existing list. So once a step is
// added (e.g. connect_your_email), a saved list is missing it — skip / reset
// / complete become no-ops (findIndex returns -1) and the total is wrong.
//
// Reconcile the saved list to the current steps while never losing progress:
//   - operate on localStorage, the copy the composable actually reads on load
//     (checking the server instead would let a reconciled browser and a stale
//     browser keep overwriting each other);
//   - order the currently-visible steps to match the UI and preserve their
//     completion by name; new steps start incomplete;
//   - keep steps that are saved but not currently visible (e.g. role-only steps
//     when the role is temporarily absent) so a role change can't erase them;
//   - skip entirely once onboarding is finished, so a completed checklist is
//     never rewritten or reopened.
// It is idempotent: an already-reconciled list produces no change.
const ONBOARDING_KEY = 'frappecrm_onboarding_status'

async function reconcileOnboarding(currentSteps) {
  // `user` is the unwrapped session user id string (Pinia unwraps the ref on
  // destructure) — the same key the composable uses. Not user.value.
  let store
  try {
    store = JSON.parse(localStorage.getItem('onboardingStatus') || '{}')
  } catch {
    return
  }
  const persisted = store?.[user]?.[ONBOARDING_KEY]
  if (!persisted?.length) return // composable seeds an empty list itself
  if (persisted.every((s) => s.completed)) return // finished: leave untouched

  const doneByName = new Map(persisted.map((s) => [s.name, s.completed]))
  const currentNames = new Set(currentSteps.map((s) => s.name))
  const visible = currentSteps.map((s) => ({
    name: s.name,
    completed: doneByName.get(s.name) ?? false,
  }))
  // Preserve saved-but-not-visible steps (e.g. manager-only steps for a user
  // whose role was removed) so their completion survives role changes.
  // Drop steps that no longer exist so they can't block completion.
  const knownNames = new Set(steps.map((s) => s.name))
  const hidden = persisted.filter(
    (s) => !currentNames.has(s.name) && knownNames.has(s.name),
  )
  const merged = [...visible, ...hidden]

  const unchanged =
    merged.length === persisted.length &&
    merged.every(
      (m, i) =>
        persisted[i]?.name === m.name &&
        persisted[i]?.completed === m.completed,
    )
  if (unchanged) return

  store[user][ONBOARDING_KEY] = merged
  try {
    localStorage.setItem('onboardingStatus', JSON.stringify(store))
    await call('frappe.onboarding.update_user_onboarding_status', {
      steps: JSON.stringify(merged),
      appName: 'frappecrm',
    })
  } catch {
    return
  }
  // Reload once so the composable re-reads the reconciled list. Only reached
  // while onboarding is unfinished (completed users returned above), so a
  // finished checklist is never reopened.
  window.location.reload()
}

async function getFirstDeal() {
  return await getFirstRecord('firstDeal', 'crm.api.onboarding.get_first_deal')
}

// the cached id may point to a record that was deleted (or a lead that was
// converted) since it was stored, so let the server validate it and fall back
async function getFirstRecord(key, method) {
  let storageKey = key + user
  let cached = localStorage.getItem(storageKey)
  let name = await call(method, { name: cached })
  if (name) {
    localStorage.setItem(storageKey, name)
  } else {
    localStorage.removeItem(storageKey)
  }
  return name
}

const showIntermediateModal = ref(false)
const currentStep = ref({})

const steps = reactive([
  // Leads are gone (#72): the first step creates a card in a funnel
  {
    name: 'create_first_deal',
    title: __('Create your first card'),
    icon: markRaw(DealsIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      router.push({ name: 'Deals', params: { viewType: 'kanban' } })
      send('trigger_deal_create', true)
      capture('onboarding_step_clicked_create_first_deal')
    },
  },
  {
    name: 'connect_your_email',
    title: __('Connect your email'),
    icon: markRaw(EmailIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      showSettings.value = true
      activeSettingsPage.value = __('Accounts')
      capture('onboarding_step_clicked_connect_your_email')
    },
    condition: () => isManager(),
  },
  {
    name: 'invite_your_team',
    title: __('Invite your team'),
    icon: markRaw(InviteIcon),
    completed: false,
    onClick: () => {
      minimize.value = true
      showSettings.value = true
      activeSettingsPage.value = 'Invite User'
      capture('onboarding_step_clicked_invite_your_team')
    },
    condition: () => isManager(),
  },
  {
    name: 'create_first_task',
    title: __('Schedule a follow-up task'),
    icon: markRaw(TaskIcon),
    completed: false,
    onClick: async () => {
      minimize.value = true
      let deal = await getFirstDeal()
      capture('onboarding_step_clicked_create_first_task')

      if (deal) {
        router.push({
          name: 'Deal',
          params: { dealId: deal },
          hash: '#tasks',
        })
      } else {
        router.push({ name: 'Tasks' })
      }
    },
  },
])

onMounted(async () => {
  if (props.mobile) return

  await users.promise

  const filteredSteps = steps.filter((step) => {
    if (step.condition) {
      return step.condition()
    }
    return true
  })

  // Bring an existing saved checklist in line with the current steps (adds
  // newly introduced steps, preserves completion). No-op when already aligned.
  await reconcileOnboarding(filteredSteps)
  setUp(filteredSteps)
  // the getting-started panel opened by itself on every page and covered the
  // screen (credtech#206); it now opens only from the sidebar banner
  showHelpModal.value = false
  flushPendingSteps()
})

// help center: the CRM's articles pointed at the original project's docs;
// Cred Hub has no public docs yet, so the list stays empty
const articles = ref([])
</script>

<style scoped>
/* Figma Lucide icons: 16px with a 1.4px line. frappe-ui draws Lucide at
   stroke-width 1.5 of 24 (1px at 16px), which looked thin; 2.1 of 24 = 1.4px. */
.ct-sidebar-icons :deep(svg),
.ct-sidebar-toggle :deep(svg) {
  stroke-width: 2.1;
}
/* Figma item text: Inter 14/20 Regular, no extra tracking (frappe-ui text-sm
   is 13px with 0.26px tracking) */
.ct-sidebar-label {
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0;
}
/* Figma "Botão recolher" / "Botão expandir": 28px circle with a light border */
.ct-sidebar-toggle {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 999px;
  border: 1px solid var(--ct-border);
  background: var(--ct-bg-page);
  color: var(--ct-text-primary);
  transition: background-color 150ms;
}
.ct-sidebar-toggle:hover {
  background: var(--ct-bg-soft);
}
</style>
