<template>
  <SettingsLayoutBase
    v-if="user.doc"
    :title="__('Profile')"
    :description="__('Manage your profile & login information.')"
  >
    <template #content>
      <!-- Figma "Configurações · Perfil" (823:2): 40px avatar, name 16/500
           with a pencil, e-mail below; divider; "Dados da conta e
           segurança" rows -->
      <div class="flex items-center justify-between gap-2">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="(file) => updateImage(file.file_url)"
        >
          <template #default="{ openFileSelector, error: _error, uploading }">
            <div class="flex items-center justify-center gap-3">
              <div class="group relative !size-10">
                <Avatar
                  class="!size-10"
                  :image="user.doc.user_image"
                  :label="fullName"
                />
                <div
                  class="absolute -bottom-0.5 -right-0.5 flex rounded-full bg-surface-elevation-2 p-0.5"
                >
                  <AvailabilityDot class="!size-3" />
                </div>
                <Tooltip
                  :hoverDelay="0"
                  side="bottom"
                  :text="profileTooltipText"
                >
                  <div
                    class="z-1 absolute top-0 left-0 flex h-9 cursor-pointer items-center justify-center rounded-full !size-10"
                    @click.stop="openFileSelector"
                  />
                  <div
                    v-if="user.doc.user_image"
                    class="z-1 size-4 absolute -top-1 -right-1 flex cursor-pointer items-center justify-center rounded-full bg-surface-base opacity-0 duration-300 ease-in-out group-hover:opacity-100 hover:bg-surface-gray-2 outline outline-black-overlay-50"
                    @click.stop="updateImage()"
                    @mouseenter="isHoveringRemove = true"
                    @mouseleave="isHoveringRemove = false"
                  >
                    <span
                      class="lucide-x size-3.5 cursor-pointer text-ink-gray-4"
                      aria-hidden="true"
                    />
                  </div>
                </Tooltip>
                <div
                  v-if="uploading"
                  class="w-full h-full top-0 left-0 absolute bg-black bg-opacity-20 rounded-full flex items-center justify-center"
                >
                  <LoadingIndicator class="size-4" />
                </div>
              </div>
              <div class="flex flex-col gap-1">
                <div class="flex flex-col gap-0.5">
                  <div v-if="!editName" class="flex items-center gap-1">
                    <span class="text-lg font-medium leading-6 text-ink-gray-9">
                      {{ fullName }}
                    </span>
                    <!-- Figma "Minha conta" (2323:12889): black 14px
                         pencil, 6px after the name -->
                    <Button
                      class="!px-0.5 !h-5"
                      variant="ghost"
                      :aria-label="__('Edit')"
                      @click="editFullName"
                    >
                      <span
                        class="lucide-pencil size-3.5 text-ink-gray-9"
                        aria-hidden="true"
                      />
                    </Button>
                  </div>
                  <div v-else class="flex items-center gap-1">
                    <TextInput
                      ref="fullNameRef"
                      v-model="fullName"
                      @keydown.enter="save"
                      @keydown.esc.stop="editName = false"
                    />
                    <Button
                      variant="outline"
                      icon="lucide-check"
                      @click="save"
                    />
                  </div>
                  <span class="text-base text-ink-gray-6">
                    {{ user.doc.email }}
                  </span>
                </div>
                <ErrorMessage :message="__(_error)" />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <SettingsDivider class="my-6" />
      <div class="flex flex-col gap-6">
        <div class="text-lg font-medium leading-6 text-ink-gray-9">
          {{ __('Account Info & Security') }}
        </div>
        <SettingsRow :label="__('Availability')">
          <template #description>
            {{
              __(
                "Set your availability so your team knows when you're reachable.",
              )
            }}
          </template>
          <AvailabilitySelect />
        </SettingsRow>
        <SettingsRow
          :label="__('Emails & Signature')"
          :description="
            __(
              'Manage your account emails and email signature for communication.',
            )
          "
        >
          <Button
            variant="outline"
            :label="__('Configure')"
            @click="emit('updateStep', 'user-email-settings')"
          />
        </SettingsRow>
        <SettingsRow
          :label="__('Password')"
          :description="__('Change your account password for security.')"
        >
          <Button
            variant="outline"
            :label="__('Change Password')"
            @click="showChangePasswordModal = true"
          />
        </SettingsRow>
      </div>
    </template>
  </SettingsLayoutBase>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import ChangePasswordModal from '@/components/Modals/ChangePasswordModal.vue'
import AvailabilitySelect from './AvailabilitySelect.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { validateIsImageFile } from '@/utils'
import {
  Avatar,
  TextInput,
  FileUploader,
  LoadingIndicator,
  toast,
  Tooltip,
  createDocumentResource,
} from 'frappe-ui'
import { ref, computed, inject, useTemplateRef, nextTick } from 'vue'

const emit = defineEmits(['updateStep'])

const { user: sessionUser } = inject('session')
const user = createDocumentResource({ doctype: 'User', name: sessionUser })

const showChangePasswordModal = ref(false)
const isHoveringRemove = ref(false)
const editName = ref(false)

const profileTooltipText = computed(() => {
  if (isHoveringRemove.value) return __('Remove Photo')
  return user.doc.user_image ? __('Change Photo') : __('Upload Photo')
})

const fullNameRef = useTemplateRef('fullNameRef')
const fullName = computed({
  get: () =>
    [user.doc.first_name, user.doc.last_name].filter(Boolean).join(' '),
  set: (val) => {
    const [firstName, ...lastName] = val.split(' ')
    user.doc.first_name = firstName
    user.doc.last_name = lastName.join(' ')
  },
})

function editFullName() {
  editName.value = true
  nextTick(() => fullNameRef.value?.focus())
}

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc)
})

function save() {
  if (!isDirty.value) {
    editName.value = false
    return
  }

  user.save.submit(null, {
    onSuccess: () => {
      editName.value = false
      toast.success(__('Profile updated successfully'))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  })
}

function updateImage(fileUrl = '') {
  isHoveringRemove.value = false
  user.doc.user_image = fileUrl
  save()
}

useKeyboardShortcuts({
  ignoreTyping: false,
  shortcuts: [
    {
      match: (e) => (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's',
      action: () => {
        if (isDirty.value) {
          save()
        }
      },
    },
  ],
})
</script>
