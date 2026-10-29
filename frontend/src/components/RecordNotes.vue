<template>
  <div class="flex flex-col gap-4 p-5" data-testid="record-notes">
    <div class="flex items-center justify-between">
      <span class="text-lg-medium text-ink-gray-8">{{ __('Notes') }}</span>
      <Button
        :label="__('New Note')"
        icon-left="lucide-plus"
        variant="solid"
        @click="showNote()"
      />
    </div>
    <div
      v-if="notes.data?.length"
      class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      <div
        v-for="note in notes.data"
        :key="note.name"
        class="group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-5 bg-surface-gray-1 px-4 py-3 hover:bg-surface-gray-2"
        :data-note="note.name"
        @click="(e) => !e.target.closest('a') && showNote(note)"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="truncate text-lg-medium text-ink-gray-8">
            {{ note.title }}
          </div>
          <Dropdown
            :options="[
              {
                label: __('Edit'),
                icon: 'lucide-edit-2',
                onClick: () => showNote(note),
              },
              {
                label: __('Delete'),
                icon: 'lucide-trash-2',
                onClick: () => deleteNote(note.name),
              },
            ]"
            @click.stop
          >
            <Button
              icon="lucide-more-horizontal"
              variant="ghost"
              :aria-label="__('More')"
            />
          </Dropdown>
        </div>
        <div
          class="flex-1 overflow-hidden text-p-sm text-ink-gray-7"
          v-html="sanitizeHTML(note.content, { ADD_ATTR: ['target'] })"
        />
        <div class="flex items-center justify-between gap-2 text-sm">
          <span class="truncate text-ink-gray-8">
            {{ getUser(note.owner).full_name }}
          </span>
          <TimelineTimestamp
            :date="note.modified"
            class-name="truncate text-sm text-ink-gray-7"
          />
        </div>
      </div>
    </div>
    <EmptyState
      v-else-if="!notes.loading"
      :icon="NoteIcon"
      :name="__('Notes')"
      :description="__('Use New Note to write something about this record.')"
    />
  </div>
</template>

<script setup>
// Notes of an organization or a contact (credtech#214): FCRM Note already
// points at any record, so they live next to the card's notes
import EmptyState from '@/components/ListViews/EmptyState.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { usersStore } from '@/stores/users'
import { sanitizeHTML } from '@/utils'
import { Dropdown, call, createResource, toast } from 'frappe-ui'
import { watch } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
})
const emit = defineEmits(['count'])

const { getUser } = usersStore()
const { showModal } = useDoctypeModal()

const notes = createResource({
  url: 'frappe.client.get_list',
  makeParams: () => ({
    doctype: 'FCRM Note',
    filters: {
      reference_doctype: props.doctype,
      reference_docname: props.docname,
    },
    fields: ['name', 'title', 'content', 'owner', 'modified'],
    order_by: 'modified desc',
    limit_page_length: 0,
  }),
  auto: true,
})

watch(
  () => notes.data,
  (data) => emit('count', data?.length || 0),
)
watch(
  () => props.docname,
  () => notes.reload(),
)

function showNote(note) {
  showModal({
    name: note?.name,
    doctype: 'FCRM Note',
    title: 'Note',
    defaults: {
      reference_doctype: props.doctype,
      reference_docname: props.docname,
    },
    callbacks: {
      afterInsert: () => notes.reload(),
      afterUpdate: () => notes.reload(),
    },
  })
}

async function deleteNote(name) {
  await toast.promise(
    call('frappe.client.delete', { doctype: 'FCRM Note', name }),
    {
      loading: __('Deleting note...'),
      success: __('Note deleted'),
      error: __('Failed to delete note'),
    },
  )
  notes.reload()
}
</script>
