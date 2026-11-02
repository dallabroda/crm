<!-- eslint-disable vue/no-v-html -->
<template>
  <!-- Figma "Notificações · Lista" (817:2): page title, "Marcar tudo como
       lido" as the primary action, rows with a blue unread dot, avatar,
       14 Medium text and the time below. -->
  <LayoutHeader>
    <template #left-header>
      <h1 class="truncate text-[20px] font-semibold leading-7 text-ink-gray-9">
        {{ __('Notifications') }}
      </h1>
    </template>
    <template #right-header>
      <Button
        v-if="notifications.data?.length"
        variant="solid"
        :label="__('Mark all as read')"
        iconLeft="lucide-check-check"
        @click="() => mark_as_read.reload()"
      />
    </template>
  </LayoutHeader>
  <div class="flex flex-1 flex-col overflow-hidden text-ink-gray-9">
    <div
      v-if="notifications.data?.length"
      class="overflow-y-auto px-3 pt-2 text-base sm:px-6"
    >
      <RouterLink
        v-for="n in notifications.data"
        :key="n.comment"
        :to="getRoute(n)"
        class="flex cursor-pointer items-start gap-3 border-b border-[var(--ct-border-soft)] px-2.5 py-3 transition-colors last:border-b-0 hover:bg-[var(--ct-bg-soft)]"
        @click="mark_doc_as_read(n.comment || n.notification_type_doc)"
      >
        <div class="flex h-7 shrink-0 items-center gap-2.5">
          <div
            class="size-2 rounded-full"
            :class="[n.read ? 'bg-transparent' : 'bg-[var(--ct-accent)]']"
          />
          <WhatsAppIcon v-if="n.type == 'WhatsApp'" class="size-7" />
          <UserAvatar v-else :user="n.from_user.name" size="lg" />
        </div>
        <div class="min-w-0 flex-1 pt-0.5">
          <div
            v-if="n.notification_text"
            class="font-medium leading-5 [&_*]:!text-ink-gray-9"
            v-html="sanitizeHTML(n.notification_text)"
          />
          <div v-else class="mb-2 space-x-1 font-medium leading-5">
            <span>{{ n.from_user.full_name }}</span>
            <span>
              {{ __('mentioned you in {0}', [n.reference_doctype]) }}
            </span>
            <span>{{ n.reference_name }}</span>
          </div>
          <div class="text-base text-ink-gray-6">
            {{ __(timeAgo(n.creation)) }}
          </div>
        </div>
      </RouterLink>
    </div>
    <EmptyState
      v-else
      name="Notifications"
      :icon="BellIcon"
      :title="__('No New Notifications')"
      :description="
        __(
          'When someone mentions you or assigns you a deal or a task, the notice shows up here.',
        )
      "
    />
  </div>
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import BellIcon from '~icons/lucide/bell'
import UserAvatar from '@/components/UserAvatar.vue'
import { notifications, notificationsStore } from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo, sanitizeHTML } from '@/utils'
import { onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, mark_doc_as_read } = notificationsStore()

onBeforeUnmount(() => {
  $socket.off('crm_notification')
})

onMounted(() => {
  $socket.on('crm_notification', () => {
    notifications.reload()
  })
})

function getRoute(notification) {
  let params = {
    leadId: notification.reference_name,
  }
  if (notification.route_name === 'Deal') {
    params = {
      dealId: notification.reference_name,
    }
  }
  return {
    name: notification.route_name,
    params: params,
    hash: notification.hash,
  }
}
</script>
