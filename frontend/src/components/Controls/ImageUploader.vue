<template>
  <FileUploader
    :file-types="image_type"
    @success="(file) => emit('upload', file.file_url)"
  >
    <template #default="{ progress, uploading, openFileSelector }">
      <div class="flex items-end space-x-1">
        <!-- Figma "Configurações · Marca": white button, blue text (comment
             1992551960, applied to every upload button of the settings) -->
        <Button
          variant="outline"
          class="ct-btn-accent-text"
          :iconLeft="uploading ? 'lucide-cloud-upload' : ImageUpIcon"
          :label="
            uploading
              ? __('Uploading {0}%', [progress])
              : image_url
                ? __('Change image')
                : __('Upload')
          "
          @click="openFileSelector"
        />
        <Button
          v-if="image_url"
          :label="__('Remove')"
          @click="emit('remove')"
        />
      </div>
    </template>
  </FileUploader>
</template>
<script setup>
import ImageUpIcon from '~icons/lucide/image-up'
import { FileUploader, Button } from 'frappe-ui'

defineProps({
  image_url: { type: String, default: '' },
  image_type: { type: String, default: 'image/*' },
})
const emit = defineEmits(['upload', 'remove'])
</script>
