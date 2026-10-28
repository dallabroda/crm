<template>
  <div
    class="flex flex-col gap-4 px-3 pb-3 pt-1"
    data-testid="organization-contacts"
  >
    <FormControl
      v-if="data.organizations"
      type="select"
      :label="__('Show contacts from')"
      :options="choices"
      :model-value="data.contacts_from"
      @update:model-value="choose"
    />
    <div
      v-for="org in data.organizations || []"
      :key="org.role"
      class="flex flex-col gap-1"
      :data-role="org.role"
    >
      <div class="flex items-baseline justify-between gap-2 px-1">
        <span class="shrink-0 text-sm text-ink-gray-5">{{ org.label }}</span>
        <router-link
          class="truncate text-base-medium text-ink-gray-8 hover:underline"
          :to="{ name: 'Organization', params: { organizationId: org.name } }"
        >
          {{ org.name }}
        </router-link>
      </div>
      <div
        v-for="row in rows(org)"
        :key="row.key"
        class="flex items-center gap-2 rounded px-1 py-1 hover:bg-surface-gray-2"
      >
        <div class="flex min-w-0 flex-1 flex-col">
          <span class="truncate text-base text-ink-gray-8">{{ row.name }}</span>
          <span class="truncate text-sm text-ink-gray-5">
            {{ [row.phone, row.email].filter(Boolean).join(' · ') }}
          </span>
        </div>
        <Button
          v-if="row.phone"
          variant="ghost"
          icon="lucide-phone"
          :tooltip="__('Call')"
          :aria-label="__('Call')"
          @click="call(row.phone)"
        />
        <Button
          v-if="row.phone"
          variant="ghost"
          icon="lucide-message-circle"
          :tooltip="__('Send WhatsApp')"
          :aria-label="__('Send WhatsApp')"
          @click="whatsappTo = row"
        />
        <Button
          v-if="row.email"
          variant="ghost"
          icon="lucide-mail"
          :tooltip="__('Send an Email')"
          :aria-label="__('Send an Email')"
          :link="`mailto:${row.email}`"
        />
      </div>
      <p v-if="!rows(org).length" class="px-1 text-p-sm text-ink-gray-5">
        {{ __('No contacts in this organization yet.') }}
      </p>
    </div>
    <SmartChatWhatsAppModal
      v-if="whatsappTo"
      :open="Boolean(whatsappTo)"
      :deal="deal"
      :phone="whatsappTo.phone"
      :name="whatsappTo.contactName"
      @update:open="(v) => !v && (whatsappTo = null)"
      @sent="$emit('sent')"
    />
  </div>
</template>

<script setup>
import { callEnabled } from '@/composables/telephony'
import { globalStore } from '@/stores/global'
import { FormControl, call as apiCall, createResource, toast } from 'frappe-ui'
import SmartChatWhatsAppModal from '@/components/Modals/SmartChatWhatsAppModal.vue'
import { computed, ref, watch } from 'vue'

// Contacts of a card with two organizations (dynamic forms phase 4,
// credtech#195): for each chosen organization, its Receita phone and e-mail
// and its people, with call, WhatsApp and e-mail shortcuts.
const props = defineProps({
  deal: { type: String, required: true },
  // changes when the card's organizations or choice change: reload
  version: { type: String, default: '' },
})

const { makeCall } = globalStore()
defineEmits(['sent'])

// contact row whose WhatsApp window is open (sent through SmartChat, credtech#211)
const whatsappTo = ref(null)

const contacts = createResource({
  url: 'crm.api.card_contacts.get_card_contacts',
  params: { deal: props.deal },
  auto: true,
})
const data = computed(() => contacts.data || {})

watch(
  () => props.version,
  () => contacts.reload(),
)

const choices = computed(() => [
  { label: __('Organization'), value: 'Organization' },
  {
    label: data.value.second_organization_label || __('Second organization'),
    value: 'Second organization',
  },
  { label: __('Both'), value: 'Both' },
])

function rows(org) {
  let list = []
  if (org.registry_phone || org.registry_email) {
    list.push({
      key: 'registry',
      name: __('Receita record'),
      // the company itself: SmartChat names the new contact after it
      contactName: org.name,
      phone: org.registry_phone,
      email: org.registry_email,
    })
  }
  for (let c of org.contacts || []) {
    list.push({
      key: c.name,
      name: c.full_name || c.name,
      contactName: c.full_name || c.name,
      phone: c.mobile_no || c.phone,
      email: c.email_id,
    })
  }
  return list
}

function call(number) {
  if (callEnabled.value) makeCall(number)
  else window.location.href = `tel:${number}`
}

async function choose(value) {
  try {
    await apiCall('frappe.client.set_value', {
      doctype: 'CRM Deal',
      name: props.deal,
      fieldname: 'contacts_from',
      value,
    })
    contacts.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the choice'))
  }
}
</script>
