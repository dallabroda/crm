<template>
  <!-- Figma 799:2 "Comentários": in the filtered tab each comment is a card
       (first line as title, the rest below, author and time in the footer) -->
  <div
    v-if="card"
    :id="activity.name"
    class="activity flex min-h-[164px] flex-col gap-2 rounded-[var(--ct-radius-md)] bg-[var(--ct-bg-soft)] p-4"
    data-testid="comment-card"
  >
    <div
      v-if="cardParts.title || (isOwner && !editing)"
      class="flex items-center justify-between gap-2"
    >
      <div
        class="min-w-0 truncate text-[16px] font-medium leading-6 text-ink-gray-9"
      >
        {{ cardParts.title }}
      </div>
      <Dropdown
        v-if="isOwner && !editing"
        :options="menuOptions"
        align="end"
        @update:open="(open) => open && (confirmingDelete = false)"
      >
        <Button
          icon="lucide-more-horizontal"
          variant="ghost"
          class="!h-6 !w-6 shrink-0"
        />
      </Dropdown>
    </div>
    <template v-if="editing">
      <RichTextField
        :content="editContent"
        editor-class="prose-sm max-w-none min-h-[3rem]"
        @change="editContent = $event"
      />
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="cancelEdit" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          @click="saveEdit"
        />
      </div>
    </template>
    <template v-else>
      <!-- the content went through sanitizeHTML() (DOMPurify) -->
      <!-- eslint-disable vue/no-v-html -->
      <div
        v-if="cardParts.body"
        class="prose-f prose-sm text-p-base line-clamp-4 max-w-none text-ink-gray-6 [&>*:first-child]:mt-0"
        v-html="cardParts.body"
      />
      <!-- eslint-enable vue/no-v-html -->
      <div v-if="activity.attachments?.length" class="flex flex-wrap gap-2">
        <AttachmentItem
          v-for="a in activity.attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="a.file_url"
        />
      </div>
    </template>
    <div
      class="mt-auto flex min-w-0 items-center gap-2 border-t border-[var(--ct-border-soft)] pt-3"
    >
      <UserAvatar :user="activity.owner" size="xs" />
      <span class="truncate text-base text-ink-gray-9">
        {{ activity.owner_name }}
      </span>
      <TimelineTimestamp
        :date="activity.creation"
        class-name="shrink-0 text-base text-ink-gray-5"
      />
    </div>
  </div>
  <div v-else :id="activity.name">
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <UserAvatar class="mr-1" :user="activity.owner" size="md" />
        <span class="text-ink-gray-9">
          {{ activity.owner_name }}
        </span>
        <span>{{ __('added a') }}</span>
        <span class="max-w-xs truncate text-ink-gray-9">
          {{ __('comment') }}
        </span>
      </div>
      <div class="ml-auto flex items-center gap-1 whitespace-nowrap">
        <TimelineTimestamp :date="activity.creation" />
        <Dropdown
          v-if="isOwner && !editing"
          :options="menuOptions"
          align="end"
          @update:open="(open) => open && (confirmingDelete = false)"
        >
          <Button
            icon="lucide-more-horizontal"
            variant="ghost"
            class="!h-6 !w-6"
          />
        </Dropdown>
      </div>
    </div>
    <div
      class="rounded-4 bg-surface-gray-1 px-3 py-[7.5px] text-base leading-6 transition-all duration-300 ease-in-out"
    >
      <template v-if="editing">
        <RichTextField
          :content="editContent"
          editor-class="prose-sm max-w-none min-h-[3rem]"
          @change="editContent = $event"
        />
        <div class="mt-2 flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="cancelEdit" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="saveEdit"
          />
        </div>
      </template>
      <template v-else>
        <!-- eslint-disable vue/no-v-html -->
        <div
          class="prose-f"
          v-html="sanitizeHTML(activity.content, { ADD_ATTR: ['target'] })"
        />
        <!-- eslint-enable vue/no-v-html -->
        <div
          v-if="activity.attachments?.length"
          class="mt-2 flex flex-wrap gap-2"
        >
          <AttachmentItem
            v-for="a in activity.attachments"
            :key="a.file_url"
            :label="a.file_name"
            :url="a.file_url"
          />
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import RichTextField from '@/components/RichTextField.vue'
import { Dropdown, Button, call, toast } from 'frappe-ui'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { sanitizeHTML, ConfirmDelete } from '@/utils'
import { sessionStore } from '@/stores/session'
import { computed, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
  // the card of the filtered "Comentários" tab instead of a timeline entry
  card: { type: Boolean, default: false },
})

const emit = defineEmits(['reload'])

const { user } = sessionStore()

const isOwner = computed(() => props.activity.owner === user)

// A comment of two or more paragraphs reads as a title and its text on the
// card; a one-paragraph comment is all text
const cardParts = computed(() => {
  const html = sanitizeHTML(props.activity.content || '', {
    ADD_ATTR: ['target'],
  })
  const box = document.createElement('div')
  box.innerHTML = html
  const blocks = [...box.children].filter((el) => el.textContent.trim())
  if (blocks.length < 2) return { title: '', body: html }
  const title = blocks[0].textContent.trim()
  blocks[0].remove()
  return { title, body: box.innerHTML }
})

const editing = ref(false)
const saving = ref(false)
const editContent = ref('')
const confirmingDelete = ref(false)

const menuOptions = computed(() => [
  {
    label: __('Edit'),
    icon: 'lucide-edit-2',
    onClick: startEdit,
  },
  ...ConfirmDelete({
    onConfirmDelete: deleteComment,
    isConfirmingDelete: confirmingDelete,
  }),
])

function startEdit() {
  editContent.value = props.activity.content || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  editContent.value = ''
}

async function saveEdit() {
  if (editContent.value === props.activity.content) {
    editing.value = false
    return
  }
  saving.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'Comment',
      name: props.activity.name,
      fieldname: 'content',
      value: editContent.value,
    })
    editing.value = false
    emit('reload')
  } catch {
    toast.error(__('Failed to update comment'))
  } finally {
    saving.value = false
  }
}

async function deleteComment() {
  try {
    await call('frappe.client.delete', {
      doctype: 'Comment',
      name: props.activity.name,
    })
    emit('reload')
  } catch {
    toast.error(__('Failed to delete comment'))
  }
}
</script>
