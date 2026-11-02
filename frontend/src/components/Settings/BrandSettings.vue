<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('Brand Settings')">
      <template #description>
        {{ __('Configure your brand name, logo and favicon.') }}
      </template>
      <template #actions>
        <template v-if="settings.isDirty">
          <Button
            v-if="settings.isDirty"
            :label="__('Update')"
            variant="solid"
            :loading="settings.loading"
            @click="updateSettings"
          />
        </template>
      </template>
    </SettingsPageHeader>

    <!-- Fields -->
    <div class="flex flex-1 flex-col gap-6 overflow-y-auto">
      <!-- Brand name: 48px field with help below (Figma "Campo com ajuda") -->
      <FormControl
        v-model="settings.doc.brand_name"
        class="ct-field-48"
        type="text"
        size="lg"
        variant="outline"
        :label="__('Brand Name')"
        :description="
          __('Set the name of your brand. Appears in the left sidebar.')
        "
        :placeholder="__('Enter Brand Name')"
      />
      <SettingsDivider />

      <!-- logo -->
      <div class="flex flex-col justify-between gap-4">
        <div class="flex items-center flex-1 gap-6">
          <div
            class="flex items-center justify-center rounded-lg border border-outline-gray-2 size-20"
          >
            <img
              v-if="settings.doc?.brand_logo"
              :src="settings.doc?.brand_logo"
              alt="Logo"
              class="size-8 rounded-4"
            />
            <ImageIcon v-else class="size-5 text-ink-gray-4" />
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-9">{{
              __('Brand Logo')
            }}</span>
            <span class="text-p-base text-ink-gray-6">
              {{
                __(
                  'Appears in the left sidebar. Recommended size is 32x32 px in PNG or SVG',
                )
              }}
            </span>
          </div>
          <div>
            <ImageUploader
              image_type="image/ico"
              :image_url="settings.doc?.brand_logo"
              @upload="(url) => (settings.doc.brand_logo = url)"
              @remove="() => (settings.doc.brand_logo = '')"
            />
          </div>
        </div>
      </div>

      <!-- favicon -->
      <div class="flex flex-col justify-between gap-4">
        <div class="flex items-center flex-1 gap-6">
          <div
            class="flex items-center justify-center rounded-lg border border-outline-gray-2 size-20"
          >
            <img
              v-if="settings.doc?.favicon"
              :src="settings.doc?.favicon"
              alt="Favicon"
              class="size-8 rounded-4"
            />
            <ImageIcon v-else class="size-5 text-ink-gray-4" />
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-9">{{
              __('Favicon')
            }}</span>
            <span class="text-p-base text-ink-gray-6">
              {{
                __(
                  'Appears next to the title in your browser tab. Recommended size is 32x32 px in PNG or ICO',
                )
              }}
            </span>
          </div>
          <div>
            <ImageUploader
              image_type="image/ico"
              :image_url="settings.doc?.favicon"
              @upload="(url) => (settings.doc.favicon = url)"
              @remove="() => (settings.doc.favicon = '')"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import ImageIcon from '~icons/lucide/image'
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import { FormControl } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'

const { _settings: settings, setupBrand } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}
</script>
