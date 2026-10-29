<template>
  <div class="flex flex-col gap-2">
    <div class="text-base-medium text-ink-gray-8">
      {{ __('Extensions') }}
    </div>
    <span class="text-p-sm text-ink-gray-6">
      {{ description }}
    </span>
    <ul class="flex flex-col divide-y divide-outline-elevation-2">
      <li
        v-for="user in crmUsers"
        :key="user.name"
        class="flex items-center justify-between gap-4 py-2"
      >
        <div class="flex flex-col">
          <span class="text-p-base text-ink-gray-8">
            {{ user.full_name }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{ user.name }}
          </span>
        </div>
        <TextInput
          class="w-32"
          :model-value="extensions[user.name] || ''"
          :placeholder="__('Extension')"
          @change="saveExtension(user.name, $event.target.value)"
        />
      </li>
    </ul>
  </div>
</template>
<script setup>
// Extension (ramal) of each user at a telephony operator (credtech#268)
import { usersStore } from '@/stores/users'
import { call, createResource, TextInput, toast } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  // operator key, as in crm.integrations.voip.operators (e.g. 'api4com')
  operator: { type: String, required: true },
  description: { type: String, default: '' },
})

const API = 'crm.integrations.voip.api.'

const { users } = usersStore()

const crmUsers = computed(() =>
  (users.data?.crmUsers || []).filter((u) => u.name !== 'Administrator'),
)

const saved = createResource({
  url: API + 'get_extensions',
  params: { operator: props.operator },
  auto: true,
})

// user -> extension, kept in step with what was saved
const extensions = reactive({})
watch(
  () => saved.data,
  (rows) => Object.assign(extensions, rows || {}),
  { immediate: true },
)

async function saveExtension(user, value) {
  const previous = extensions[user] || ''
  if ((value || '').trim() === previous) return
  try {
    const result = await call(API + 'set_extension', {
      operator: props.operator,
      user,
      extension: value,
    })
    extensions[user] = result.extension
    toast.success(__('Extension saved'))
  } catch (err) {
    extensions[user] = previous
    toast.error(err.messages?.[0] || __('Something went wrong'))
  }
}
</script>
