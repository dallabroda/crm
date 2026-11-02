<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    v-if="visible"
    ref="target"
    class="absolute z-20 h-screen bg-surface-base transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      left: 'calc(100% + 1px)',
    }"
  >
    <div class="flex h-screen flex-col text-ink-gray-9">
      <div
        class="z-20 flex h-16 items-center justify-between border-b border-[var(--ct-border-soft)] pl-4 pr-3"
      >
        <div class="text-lg font-semibold text-ink-gray-9">
          {{ __('Notifications') }}
        </div>
        <div class="flex gap-1">
          <Button
            v-if="notifications.data?.length"
            :tooltip="__('Mark all as read')"
            :icon="MarkAsDoneIcon"
            variant="ghost"
            @click="markAllAsRead"
          />
          <Button
            :tooltip="__('Close')"
            icon="lucide-x"
            variant="ghost"
            @click="() => toggle()"
          />
        </div>
      </div>
      <div
        v-if="notifications.data?.length"
        class="divide-y divide-[var(--ct-border-soft)] overflow-auto text-base"
      >
        <RouterLink
          v-for="n in notifications.data"
          :key="n.comment"
          :to="getRoute(n)"
          class="flex cursor-pointer items-start gap-3 px-4 py-3 transition-colors hover:bg-[var(--ct-bg-soft)]"
          @click="markAsRead(n.comment || n.notification_type_doc)"
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
        :title="__('No New Notifications')"
        :description="
          __(
            'When someone mentions you or assigns you a deal or a task, the notice shows up here.',
          )
        "
        :icon="BellIcon"
        width="lg"
      />
    </div>
  </div>
</template>
<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import BellIcon from '~icons/lucide/bell'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  visible,
  notifications,
  notificationsStore,
} from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo, sanitizeHTML } from '@/utils'
import { onClickOutside } from '@vueuse/core'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const { $socket } = globalStore()
const { mark_as_read, toggle, mark_doc_as_read } = notificationsStore()
const { capture } = useTelemetry()

const target = ref(null)
onClickOutside(
  target,
  () => {
    if (visible.value) toggle()
  },
  {
    ignore: ['#notifications-btn'],
  },
)

function markAsRead(doc) {
  capture('notification_mark_as_read')
  mark_doc_as_read(doc)
}

function markAllAsRead() {
  capture('notification_mark_all_as_read')
  mark_as_read.reload()
}

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
