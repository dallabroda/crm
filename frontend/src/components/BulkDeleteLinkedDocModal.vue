<template>
  <Dialog v-model:open="show" :size="'xl'" bare>
    <template #default>
      <div class="px-6 pb-6">
        <div class="-mr-2 flex items-center justify-between gap-3 pb-2 pt-5">
          <div>
            <Dialog.Title as-child>
              <h3 class="text-[20px] font-semibold leading-7 text-ink-gray-9">
                {{ __('Delete') }}
              </h3>
            </Dialog.Title>
          </div>
          <div class="flex items-center gap-1">
            <Dialog.Close as-child>
              <Button
                :aria-label="__('Close')"
                variant="ghost"
                size="lg"
                icon="lucide-x"
              />
            </Dialog.Close>
          </div>
        </div>
        <div>
          <div class="text-ink-gray-5 text-base">
            {{
              __('Are you sure you want to delete {0} items?', [
                props.items?.length,
              ])
            }}
          </div>
        </div>
      </div>
      <div class="bg-[var(--ct-bg-soft)] px-6 py-4">
        <div class="flex flex-row-reverse gap-2">
          <Button
            :label="__('Delete {0} items', [props.items.length])"
            icon-left="lucide-trash-2"
            variant="solid"
            theme="red"
            @click="confirmDelete()"
          />
          <Button
            :label="__('Unlink & Delete {0} items', [props.items.length])"
            icon-left="lucide-unlock"
            variant="solid"
            @click="confirmUnlink()"
          />
        </div>
      </div>
      <div v-if="confirmDeleteInfo.show" class="px-6 pb-6">
        <div class="-mr-2 flex items-center justify-between gap-3 pb-2 pt-5">
          <div>
            <h3 class="text-[20px] font-semibold leading-7 text-ink-gray-9">
              {{ __('Delete') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Dialog.Close as-child>
              <Button
                :aria-label="__('Close')"
                variant="ghost"
                size="lg"
                icon="lucide-x"
              />
            </Dialog.Close>
          </div>
        </div>
        <div>
          <div class="text-ink-gray-5 text-base">
            {{
              confirmDeleteInfo.delete
                ? __(
                    'This will delete selected items and items linked to it, are you sure?',
                  )
                : __(
                    'This will delete selected items and unlink linked items to it, are you sure?',
                  )
            }}
          </div>
        </div>
      </div>
      <div
        v-if="confirmDeleteInfo.show"
        class="bg-[var(--ct-bg-soft)] px-6 py-4"
      >
        <div class="flex flex-row-reverse gap-2">
          <Button
            :label="
              confirmDeleteInfo.delete ? __('Delete') : __('Unlink & Delete')
            "
            :icon-left="
              confirmDeleteInfo.delete ? 'lucide-trash-2' : 'lucide-unlock'
            "
            variant="solid"
            theme="red"
            @click="deleteDocs()"
          />
          <Button
            :label="__('Cancel')"
            variant="subtle"
            @click="confirmDeleteInfo.show = false"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, call } from 'frappe-ui'
import { ref } from 'vue'

const show = defineModel({ type: Boolean })
const props = defineProps({
  doctype: { type: String, required: true },
  items: { type: Array, required: true },
  reload: { type: Function, required: true },
})

const confirmDeleteInfo = ref({
  show: false,
  title: '',
  message: '',
  delete: false,
})

const confirmDelete = () => {
  confirmDeleteInfo.value = {
    show: true,
    title: __('Delete'),
    message: __('Are you sure you want to delete {0} linked doc(s)?', [
      props.items.length,
    ]),
    delete: true,
  }
}

const confirmUnlink = () => {
  confirmDeleteInfo.value = {
    show: true,
    title: __('Unlink'),
    message: __('Are you sure you want to unlink {0} linked doc(s)?', [
      props.items.length,
    ]),
    delete: false,
  }
}

const deleteDocs = () => {
  call('crm.api.doc.delete_bulk_docs', {
    items: props.items,
    doctype: props.doctype,
    delete_linked: confirmDeleteInfo.value.delete,
  }).then(() => {
    confirmDeleteInfo.value = {
      show: false,
      title: '',
    }
    show.value = false
    props.reload()
  })
}
</script>
