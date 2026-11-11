<template>
  <!-- Figma "Card · Anexos" (2533:43700): one bordered list (8px radius);
       each row has a 36px grey file icon, the name (14 Medium), size · who
       sent it · when (12), and ghost download / delete buttons -->
  <div
    v-if="attachments.length"
    class="overflow-hidden rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-base"
  >
    <div
      v-for="attachment in attachments"
      :key="attachment.name"
      class="activity flex cursor-pointer items-center gap-3 border-b border-[var(--ct-border)] py-3 pl-4 pr-3 last:border-b-0 hover:bg-[var(--ct-bg-soft)]"
      @click="openFile(attachment)"
    >
      <div
        class="grid size-9 shrink-0 place-items-center rounded-[var(--ct-radius-sm)] bg-[var(--ct-bg-soft)] text-ink-gray-9"
      >
        <span
          :class="fileIcon(attachment.file_type)"
          class="size-[18px]"
          aria-hidden="true"
        />
      </div>
      <div class="flex min-w-0 flex-1 flex-col gap-0.5">
        <div
          class="truncate text-base font-medium leading-[17px] text-ink-gray-9"
        >
          {{ attachment.file_name }}
        </div>
        <div class="truncate text-xs leading-[15px] text-ink-gray-6">
          {{ attachmentMeta(attachment) }}
        </div>
      </div>
      <Button
        :tooltip="__('Download')"
        variant="ghost"
        icon="lucide-download"
        @click.stop="downloadFile(attachment)"
      />
      <Button
        :tooltip="__('Delete Attachment')"
        variant="ghost"
        icon="lucide-trash-2"
        class="ct-btn-danger-icon"
        @click.stop="() => deleteAttachment(attachment.name)"
      />
    </div>
  </div>
</template>
<script setup>
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { Button, call } from 'frappe-ui'
import { isImage, timeAgo } from '@/utils'
import { userLocale } from '@/utils/locale'

defineProps({
  attachments: { type: Array, default: () => [] },
})

const emit = defineEmits(['reload'])

const { $dialog } = globalStore()
const { getUser } = usersStore()

// "245 KB · Enviado por Rafael Lima · 7 horas atrás"
function attachmentMeta(attachment) {
  let parts = [fileSize(attachment.file_size)]
  if (attachment.owner) {
    let name = getUser(attachment.owner)?.full_name || attachment.owner
    parts.push(__('Enviado por {0}', [name]))
  }
  if (attachment.creation) parts.push(timeAgo(attachment.creation))
  return parts.filter(Boolean).join(' · ')
}

// "245 KB", "1,2 MB": whole kilobytes, one decimal from megabytes up, in the
// user's language
function fileSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  let units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = Number(bytes)
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  let number = new Intl.NumberFormat(userLocale(), {
    maximumFractionDigits: i >= 2 ? 1 : 0,
  }).format(size)
  return `${number} ${units[i]}`
}

function downloadFile(attachment) {
  let link = document.createElement('a')
  link.href = attachment.file_url
  link.download = attachment.file_name || ''
  link.click()
}

function openFile(attachment) {
  window.open(attachment.file_url, '_blank')
}

function deleteAttachment(fileName) {
  $dialog({
    title: __('Delete Attachment'),
    message: __('Are you sure you want to delete this attachment?'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async ({ close }) => {
          await call('frappe.client.delete', {
            doctype: 'File',
            name: fileName,
          })
          emit('reload')
          close()
        },
      },
    ],
  })
}

function fileIcon(type) {
  if (isImage(type)) return 'lucide-image'
  let audioExtentions = ['wav', 'mp3', 'ogg', 'flac', 'aac']
  let videoExtentions = ['mp4', 'avi', 'mkv', 'flv', 'mov']
  if (audioExtentions.includes(type?.toLowerCase())) return 'lucide-file-audio'
  if (videoExtentions.includes(type?.toLowerCase())) return 'lucide-file-video'
  return 'lucide-file-text'
}
</script>
