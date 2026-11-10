<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Users')">
      <template #description>
        {{
          __(
            'Invite users and choose their role to control what they can see and do.',
          )
        }}
      </template>
      <template #actions>
        <!-- Access is only by invitation (credtech#190): "New" opens the invitation -->
        <Button
          :label="__('Invite User')"
          icon-left="lucide-plus"
          variant="solid"
          @click="activeSettingsPage = 'Invite User'"
        />
      </template>
    </SettingsPageHeader>

    <!-- loading state -->
    <div v-if="users.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="users.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!users.loading && users.data?.crmUsers?.length == 1"
      name="Users"
      :description="__('Add one to get started.')"
      icon="user"
    />

    <!-- Users List -->
    <div
      v-if="!users.loading && users.data?.crmUsers?.length > 1"
      class="flex flex-col overflow-hidden"
    >
      <div
        v-if="users.data?.crmUsers?.length > 10"
        class="flex items-center gap-2 mb-4 pt-0.5"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search User')"
          class="w-full"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <Select
          v-model="currentRole"
          class="shrink-0"
          :options="[
            { label: __('All'), value: 'All' },
            { label: __('Admin'), value: 'System Manager' },
            { label: __('Manager'), value: 'Sales Manager' },
            { label: __('Sales User'), value: 'Sales User' },
          ]"
        />
      </div>
      <ul
        class="divide-y divide-outline-gray-1 overflow-y-auto rounded-lg border border-outline-gray-1"
      >
        <template v-for="user in usersList" :key="user.name">
          <!-- Figma "Configurações · Usuários" row: 32px avatar, name 14
               Medium over e-mail 14 Regular, "Filtro" and a ghost "…" -->
          <li class="flex items-center justify-between gap-3 px-4 py-3">
            <div class="flex min-w-0 items-center">
              <div class="relative shrink-0">
                <Avatar
                  :image="user.user_image"
                  :label="user.full_name"
                  size="xl"
                />
                <div
                  class="absolute -bottom-0.5 -right-0.5 flex rounded-full bg-surface-elevation-2 p-0.5"
                >
                  <AvailabilityDot :user="user.name" class="!size-2.5" />
                </div>
              </div>
              <div class="flex flex-col ml-3">
                <div
                  class="flex items-center text-[14px] font-medium leading-5 text-[var(--ct-text-primary)]"
                >
                  {{ user.full_name }}
                </div>
                <div
                  class="mt-0.5 text-[14px] leading-5 text-[var(--ct-text-secondary)]"
                >
                  {{ user.name }}
                </div>
              </div>
            </div>
            <div class="flex flex-row-reverse items-center gap-3">
              <Dropdown
                :options="getMoreOptions(user)"
                :button="{
                  icon: 'lucide-more-horizontal',
                  variant: 'ghost',
                  class: 'size-8',
                  onblur: (e) => {
                    e.stopPropagation()
                    confirmRemove = false
                  },
                }"
                align="end"
              />
              <!-- Figma "Configurações · Usuários": the role is a "Filtro"
                   select (border, label and chevron, no leading icon) -->
              <Tooltip
                v-if="isManager() && user.role == 'System Manager'"
                :text="__('Cannot change role of user with Admin access')"
              >
                <button type="button" class="ct-filter" disabled>
                  <span class="truncate">{{ __('Admin') }}</span>
                </button>
              </Tooltip>
              <Dropdown v-else :options="getDropdownOptions(user)" align="end">
                <template #default="{ open }">
                  <button type="button" class="ct-filter">
                    <span class="truncate">{{ roleMap[user.role] }}</span>
                    <span
                      class="size-4 shrink-0"
                      :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                      aria-hidden="true"
                    />
                  </button>
                </template>
              </Dropdown>
            </div>
          </li>
        </template>
        <!-- Load More Button -->
        <div
          v-if="!users.loading && users.hasNextPage"
          class="flex justify-center"
        >
          <Button
            class="mt-3.5 p-2"
            :loading="users.loading"
            :label="__('Load More')"
            icon-left="lucide-refresh-cw"
            @click="() => users.next()"
          />
        </div>
      </ul>
    </div>
  </div>
</template>

<script setup>
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import {
  Dropdown,
  Avatar,
  TextInput,
  toast,
  call,
  Tooltip,
  Select,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { ConfirmDelete } from '../../utils'

const { users, isAdmin, isManager } = usersStore()

const searchRef = ref(null)
const search = ref('')
const currentRole = ref('All')

const roleMap = {
  'System Manager': __('Admin'),
  'Sales Manager': __('Manager'),
  'Sales User': __('Sales User'),
}

const usersList = computed(() => {
  let filteredUsers =
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || []

  return filteredUsers
    .filter(
      (user) =>
        user.name?.includes(search.value) ||
        user.full_name?.includes(search.value),
    )
    .filter((user) => {
      if (currentRole.value === 'All') return true
      return user.role === currentRole.value
    })
})

const confirmRemove = ref(false)

function getMoreOptions(user) {
  return [
    ...ConfirmDelete({
      onConfirmDelete: () => removeUser(user),
      isConfirmingDelete: confirmRemove,
      label: __('Remove'),
    }),
  ]
}

function getDropdownOptions(user) {
  let options = [
    {
      label: __('Admin'),
      icon: 'lucide-shield',
      selected: user.role === 'System Manager',
      onClick: () => updateRole(user, 'System Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Manager'),
      icon: 'lucide-briefcase',
      selected: user.role === 'Sales Manager',
      onClick: () => updateRole(user, 'Sales Manager'),
      condition: () => isAdmin(),
    },
    {
      label: __('Sales User'),
      icon: 'lucide-user-check',
      selected: user.role === 'Sales User',
      onClick: () => updateRole(user, 'Sales User'),
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}

function updateRole(user, newRole) {
  if (user.role === newRole) return

  call('crm.api.user.update_user_role', {
    user: user.name,
    new_role: newRole,
  })
    .then(() => {
      toast.success(
        __('{0} has been granted {1} access', [
          user.full_name,
          roleMap[newRole],
        ]),
      )
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

function removeUser(user) {
  call('crm.api.user.remove_crm_roles_from_user', {
    user: user.name,
  })
    .then(() => {
      toast.success(__('User {0} has been removed', [user.full_name]))
      users.reload()
    })
    .catch((e) => {
      toast.error(e?.messages?.[0] || __('Something went wrong'))
    })
}

onMounted(() => {
  if (searchRef.value) {
    searchRef.value.focus()
  }
})
</script>
