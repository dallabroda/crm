<template>
  <div
    v-if="title !== 'Data'"
    class="mx-3 my-3 flex flex-col gap-2.5 sm:mx-6 sm:mb-4 sm:mt-6"
  >
    <div class="flex items-center justify-between text-lg-medium">
      <!-- Figma "Card · Atividade": section title 18 Semi Bold, blue "Novo ˅"
           (no plus icon on the activity tab) -->
      <div
        class="flex h-8 items-center text-[18px] font-semibold leading-6 text-ink-gray-9"
      >
        {{ inActivityTab ? __('Atividades') : __(title) }}
      </div>
      <div class="flex items-center gap-2">
        <!-- Figma 799:2 / 801:2 / 802:2: a filtered activity tab keeps the
             single primary "Novo ˅"; its actions live inside that dropdown -->
        <template v-if="inActivityTab" />
        <Button
          v-else-if="title == 'Emails'"
          variant="solid"
          :label="__('New Email')"
          iconLeft="lucide-plus"
          @click="emailBox.openEmailBox()"
        />
        <Button
          v-else-if="title == 'Comments'"
          variant="solid"
          :label="__('Novo comentário')"
          iconLeft="lucide-plus"
          @click="emailBox.openCommentBox()"
        />
        <Button
          v-else-if="title == 'Calls' && doc?.mobile_no"
          variant="solid"
          :label="callEnabled ? __('Fazer Ligação (Integração)') : __('Ligar (Telefone)')"
          :iconLeft="PhoneIcon"
          @click="initiateCall"
        />
        <Button
          v-else-if="title == 'Tasks'"
          variant="solid"
          :label="__('New Task')"
          iconLeft="lucide-plus"
          @click="modalRef.showTask()"
        />
        <Button
          v-else-if="title == 'Attachments'"
          variant="solid"
          :label="__('Enviar anexo')"
          iconLeft="lucide-upload"
          @click="showFilesUploader = true"
        />
        <div v-else-if="title == 'WhatsApp'" class="flex gap-2 shrink-0">
          <Button
            :label="__('Send Template')"
            @click="showWhatsappTemplates = true"
          />
          <Button
            variant="solid"
            :label="__('New Message')"
            iconLeft="lucide-plus"
            @click="whatsappBox.show()"
          />
        </div>
        <!-- Figma "Card · Atividades": one "Filtro" select ("Todas as
             atividades ˅") next to "Novo" instead of the row of pills -->
        <Dropdown
          v-if="activeTab === 'activity'"
          :options="filterOptions"
          align="end"
        >
          <template #default="{ open }">
            <button type="button" class="ct-filter">
              <span class="truncate">{{ activeFilterLabel }}</span>
              <span
                class="size-4 shrink-0"
                :class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
                aria-hidden="true"
              />
            </button>
          </template>
        </Dropdown>
        <Dropdown
          v-if="
            inActivityTab ||
            !['Quotations', 'WhatsApp', 'Attachments'].includes(title)
          "
          :options="defaultActions"
          @click.stop
        >
          <template #default="{ open }">
            <Button
              :variant="inActivityTab ? 'solid' : 'outline'"
              class="flex items-center gap-1"
              :label="__('New')"
              :iconLeft="inActivityTab ? undefined : 'lucide-plus'"
              :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            />
          </template>
        </Dropdown>
      </div>
    </div>

  </div>
</template>
<script setup>
import MultiActionButton from '@/components/MultiActionButton.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { globalStore } from '@/stores/global'
import { whatsappEnabled } from '@/composables/whatsapp'
import { callEnabled } from '@/composables/telephony'
import { Dropdown, toast } from 'frappe-ui'
import { computed, h } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  doctype: { type: String, default: '' },
  modalRef: { type: Object, default: () => ({}) },
  whatsappBox: { type: Object, default: () => ({}) },
})

const { makeCall } = globalStore()

// the card a call is made from goes with it, so it lands on its timeline
const dealName = () =>
  props.doctype === 'CRM Deal' ? props.doc.name || null : null

const activeTab = defineModel({ type: String })
const activityFilter = defineModel('activityFilter', {
  type: String,
  default: 'Activity',
})
const showWhatsappTemplates = defineModel('showWhatsappTemplates', {
  type: Boolean,
})
const showFilesUploader = defineModel('showFilesUploader', { type: Boolean })
const emailBox = defineModel('emailBox', { type: Object, default: () => ({}) })

// the activity tab, whatever its filter (Comentários, Tarefas, Ligações...)
const inActivityTab = computed(() => activeTab.value === 'activity')

const filterPills = computed(() => [
  { value: 'Activity', label: __('Todas as atividades') },
  { value: 'Comments', label: __('Comentários') },
  { value: 'Emails', label: __('E-mails') },
  { value: 'Calls', label: __('Ligações') },
  { value: 'Tasks', label: __('Tarefas') },
  { value: 'Attachments', label: __('Anexos') },
])

const filterOptions = computed(() =>
  filterPills.value.map((pill) => ({
    label: pill.label,
    onClick: () => (activityFilter.value = pill.value),
  })),
)
const activeFilterLabel = computed(
  () =>
    filterPills.value.find((pill) => pill.value === activityFilter.value)
      ?.label || filterPills.value[0].label,
)

const defaultActions = computed(() => {
  let actions = [
    {
      icon: h(CommentIcon, { class: 'h-4 w-4' }),
      label: __('Comentário'),
      onClick: () => emailBox.value.openCommentBox(),
    },
    {
      icon: h(Email2Icon, { class: 'h-4 w-4' }),
      label: __('Email'),
      onClick: () => emailBox.value.openEmailBox(),
    },
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: callEnabled.value ? __('Fazer Ligação (Integração)') : __('Ligar (Telefone)'),
      onClick: initiateCall,
      condition: () => Boolean(props.doc?.mobile_no),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('Task'),
      onClick: () => props.modalRef.showTask(),
    },
    {
      icon: h(AttachmentIcon, { class: 'h-4 w-4' }),
      label: __('Upload Attachment'),
      onClick: () => (showFilesUploader.value = true),
    },
    {
      icon: h(WhatsAppIcon, { class: 'h-4 w-4' }),
      label: __('WhatsApp Message'),
      onClick: () => (activeTab.value = 'whatsapp'),
      condition: () => whatsappEnabled.value,
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
})

function initiateCall() {
  let phone = props.doc.mobile_no
  if (!phone) {
    toast.error(__('No Mobile Number Set'))
    return
  }
  if (callEnabled.value) {
    makeCall(phone, dealName())
  } else {
    window.location.href = `tel:${phone}`
  }
}
</script>
