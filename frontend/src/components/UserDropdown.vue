<template>
  <!-- Figma "Barra lateral · HubTech" footer: avatar, name and e-mail of the
       signed-in user; opens the account menu. Collapsed, only the avatar. -->
  <!-- Figma "Menu da conta" (2326:41374): as wide as the footer, 10px above it -->
  <Dropdown
    :options="dropdownItems"
    side="top"
    :offset="10"
    :matchTriggerWidth="!isCollapsed"
    v-bind="$attrs"
  >
    <template #default="{ open }">
      <button
        type="button"
        class="flex w-full items-center gap-2.5 rounded-[var(--ct-radius-md)] text-left transition-colors duration-300 ease-in-out"
        :class="[
          isCollapsed ? 'justify-center' : 'py-1 pl-1.5 pr-1',
          open ? 'bg-[var(--ct-bg-soft)]' : 'hover:bg-[var(--ct-bg-soft)]',
        ]"
        :aria-label="user.full_name"
      >
        <Avatar
          :label="user.full_name"
          :image="user.user_image"
          size="xl"
          class="shrink-0"
          >{{ initials(user.full_name) }}</Avatar
        >
        <div v-if="!isCollapsed" class="flex min-w-0 flex-1 flex-col">
          <span
            class="truncate text-[14px] font-medium leading-5 tracking-normal text-ink-gray-9"
          >
            {{ user.full_name }}
          </span>
          <span
            class="truncate text-[14px] font-normal leading-5 tracking-normal text-ink-gray-6"
          >
            {{ user.email || user.name }}
          </span>
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import FrappeCloudIcon from '@/components/Icons/FrappeCloudIcon.vue'
import AppsIcon from '@/components/Icons/AppsIcon.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { getSettings } from '@/stores/settings'
import { showSettings, isMobileView } from '@/composables/settings'
import { showAboutModal } from '@/composables/modals'
import { confirmLoginToFrappeCloud } from '@/composables/frappecloud'
import { spriteIcon } from '@/utils/spriteIcon'
import { initials } from '@/utils'
import { Avatar, createResource, Dropdown } from 'frappe-ui'
import { computed, h, markRaw } from 'vue'
import { useRouter } from 'vue-router'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const { settings } = getSettings()
const { logout } = sessionStore()
const { getUser } = usersStore()
const router = useRouter()

const user = computed(() => getUser() || {})

const apps = createResource({
  url: 'frappe.apps.get_apps',
  cache: 'apps',
  auto: true,
  transform: (data) => [deskApp(), ...crmSiblingApps(data)],
})

const dropdownItems = computed(() => [
  // Figma "Menu da conta" (2326:41374): "Minha conta", a divider and "Sair".
  // Apps, Settings (it has its own sidebar entry), About and Frappe Cloud stay out.
  {
    group: 'Account',
    hideLabel: true,
    options: [
      {
        icon: 'lucide-user-round ct-account-menu-icon',
        label: __('My account'),
        onClick: () => router.push({ name: 'My Account' }),
      },
    ],
  },
  {
    group: 'Logout',
    hideLabel: true,
    options: [getStandardItem({ name1: 'logout', label: 'Log out' })],
  },
])

function dropdownItemObj(item) {
  let _item = JSON.parse(JSON.stringify(item))
  let icon = _item.icon || 'external-link'
  if (typeof icon === 'string' && icon.startsWith('<svg')) {
    icon = markRaw(h('div', { innerHTML: icon }))
  }
  _item.icon = spriteIcon(icon)

  if (_item.is_standard) {
    return getStandardItem(_item)
  }

  return {
    icon: _item.icon,
    label: __(_item.label),
    onClick: () =>
      window.open(_item.route, _item.open_in_new_window ? '_blank' : ''),
  }
}

function getStandardItem(item) {
  switch (item.name1) {
    case 'app_selector':
      return {
        icon: markRaw(AppsIcon),
        label: __(item.label),
        submenu: appMenuItems(),
      }
    case 'settings':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showSettings.value = true),
        condition: () => !isMobileView.value,
      }
    case 'login_to_fc':
      return {
        icon: h(FrappeCloudIcon),
        label: __(item.label),
        onClick: () => confirmLoginToFrappeCloud(),
        condition: () => !isMobileView.value && window.is_fc_site,
      }
    case 'about':
      return {
        icon: item.icon,
        label: __(item.label),
        onClick: () => (showAboutModal.value = true),
      }
    case 'logout':
      // Figma "Sair": red, arrow leaving to the left
      return {
        icon: 'lucide-arrow-left-from-line',
        theme: 'red',
        label: __(item.label),
        onClick: () => logout.submit(),
      }
  }
}

function appMenuItems() {
  return (apps.data || []).map((app) => ({
    label: app.title,
    onClick: () => (window.location.href = app.route),
    slots: {
      prefix: () => h('img', { class: 'size-5 rounded-4', src: app.logo }),
    },
  }))
}

function deskApp() {
  return {
    name: 'frappe',
    logo: '/assets/frappe/images/framework.png',
    title: __('Administration'),
    route: '/desk/build',
  }
}

function crmSiblingApps(data) {
  return data
    .filter((app) => app.name !== 'crm')
    .map((app) => ({
      name: app.name,
      logo: app.logo,
      title: __(app.title),
      route: app.route,
    }))
}
</script>

<style>
/* Figma "Menu da conta" (2326:41374). The menu is portaled out of this
   component, so it is found by the "Minha conta" icon it holds: 8px radius,
   #e6e7eb border, 6px padding, 36px rows (10px sides and gap, 14 Regular
   black), 2px around the divider */
.menu-content:has(.ct-account-menu-icon) {
  border: 1px solid var(--ct-border-soft);
  border-radius: var(--ct-radius-md);
  box-shadow:
    0 4px 6px rgba(16, 24, 40, 0.03),
    0 12px 16px rgba(16, 24, 40, 0.08);
}
.menu-content:has(.ct-account-menu-icon) > [data-slot='group'] {
  padding: 2px 6px;
}
.menu-content:has(.ct-account-menu-icon) > [data-slot='group']:first-child {
  padding-top: 6px;
}
.menu-content:has(.ct-account-menu-icon) > [data-slot='group']:last-child {
  padding-bottom: 6px;
}
.menu-content:has(.ct-account-menu-icon) [role='menuitem'] {
  border-radius: var(--ct-radius-sm);
}
.menu-content:has(.ct-account-menu-icon) [role='menuitem'] > * {
  height: 36px;
  gap: 10px;
  padding: 0 10px;
  font-size: 14px;
  line-height: 20px;
}
.menu-content:has(.ct-account-menu-icon) .text-ink-gray-7 {
  color: var(--ct-text-primary);
}
.menu-content:has(.ct-account-menu-icon) .text-ink-gray-6 {
  color: var(--ct-text-primary);
}
.menu-content:has(.ct-account-menu-icon) .text-ink-red-7 {
  color: var(--ct-danger);
}
</style>
