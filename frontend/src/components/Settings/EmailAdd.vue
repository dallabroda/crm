<template>
  <!-- Figma "Configurações · Contas · Configurar e-mail" (1336:21663) -->
  <div class="flex flex-col h-full gap-6">
    <SettingsPageHeader :title="__('Setup Email')">
      <template #description>
        {{ __('Choose the email service provider you want to configure.') }}
      </template>
    </SettingsPageHeader>
    <!-- email service provider selection -->
    <!-- "Provedores": one bordered tile per provider, blue when selected -->
    <div
      class="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-3 py-px"
    >
      <button
        v-for="s in services"
        :key="s.name"
        type="button"
        class="flex min-h-[94px] flex-col items-center gap-2 rounded-lg border bg-surface-base px-2 py-3 hover:bg-surface-gray-1"
        :class="
          selectedService?.name === s?.name
            ? 'border-[var(--ct-accent)] ring-1 ring-[var(--ct-accent)]'
            : 'border-[var(--ct-border)]'
        "
        @click="handleSelect(s)"
      >
        <span
          class="flex size-10 items-center justify-center rounded-full bg-[var(--ct-bg-soft)]"
        >
          <img :src="s.icon" class="size-5" />
        </span>
        <span class="text-base font-medium text-ink-gray-9">{{ s.name }}</span>
      </button>
    </div>
    <!-- Figma "Configurar e-mail" (2345:29055): notice, fields, options and
         funnel 24px apart; 516px fields (the form leaves 32px at the end) -->
    <div v-if="selectedService" class="flex flex-col gap-6">
      <!-- email service provider info -->
      <!-- Style Guide "Aviso" (960:402), with its small action button -->
      <CtAlert type="warning">
        {{ providerInfo }}
        <template #action>
          <a
            :href="selectedService.link"
            target="_blank"
            class="flex h-6 shrink-0 items-center rounded-[var(--ct-radius-sm)] bg-surface-base px-3 text-xs font-medium hover:bg-surface-gray-2"
          >
            {{ __('Learn more here') }}
          </a>
        </template>
      </CtAlert>
      <!-- service provider fields -->
      <div class="flex flex-col gap-6">
        <div class="ct-field-48 grid grid-cols-2 gap-4 pr-8">
          <div
            v-for="field in fields"
            :key="field.name"
            class="flex flex-col gap-1"
          >
            <FormControl
              v-model="state[field.name]"
              :label="field.label"
              :name="field.name"
              :type="field.type"
              :placeholder="field.placeholder"
            />
          </div>
        </div>
        <div class="ct-email-options grid grid-cols-2 gap-4 pr-8">
          <template v-for="field in switches" :key="field.name">
            <div
              v-if="field.condition ? field.condition(state) : true"
              class="flex flex-col gap-0.5"
            >
              <FormControl
                v-model="state[field.name]"
                :label="field.label"
                :name="field.name"
                :type="field.type"
              />
              <p class="pl-[26px] text-xs text-ink-gray-6">
                {{ field.description }}
              </p>
            </div>
          </template>
        </div>
        <div
          v-if="state.create_lead_from_incoming_email"
          class="ct-field-48 grid grid-cols-2 gap-4 pr-8"
        >
          <PipelineSelect v-model="state.crm_pipeline" />
        </div>
        <p
          v-if="state.create_lead_from_incoming_email"
          class="text-xs text-ink-gray-6"
        >
          {{
            __('Cards created from emails of this account go to this funnel.')
          }}
        </p>
        <ErrorMessage class="ml-1" :message="error" />
      </div>
    </div>
    <!-- action button -->
    <div
      v-if="selectedService"
      class="mt-auto flex justify-between border-t border-outline-gray-2 pt-6"
    >
      <Button
        :label="__('Back')"
        variant="outline"
        icon-left="lucide-arrow-left"
        :disabled="addEmailRes.loading"
        @click="emit('update:step', 'email-list')"
      />
      <Button
        :label="__('Create')"
        variant="solid"
        :loading="addEmailRes.loading"
        @click="createEmailAccount"
      />
    </div>
  </div>
</template>

<script setup>
import './fieldOutline.css'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import { computed, reactive, ref } from 'vue'
import { createResource, toast } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { useCrmOnboarding } from '@/composables/onboarding'
import CtAlert from '@/components/CtAlert.vue'
import {
  customProviderFields,
  popularProviderFields,
  services,
  validateInputs,
  accountSwitches,
  getSystemEmailAccounts,
} from './emailConfig'
import PipelineSelect from '@/components/Pipelines/PipelineSelect.vue'

const emit = defineEmits(['update:step'])

const state = reactive({
  service: '',
  email_account_name: '',
  email_id: '',
  password: '',
  api_key: '',
  api_secret: '',
  frappe_mail_site: '',
  enable_incoming: false,
  enable_outgoing: false,
  default_incoming: false,
  default_outgoing: false,
  create_lead_from_incoming_email: false,
  crm_pipeline: '',
})

const hasSystemAccount = ref(false)
getSystemEmailAccounts().then((names) => {
  hasSystemAccount.value = Boolean(names?.length)
})
const switches = computed(() => accountSwitches(hasSystemAccount.value))
const { capture } = useTelemetry()
const { completeStep } = useCrmOnboarding()

const selectedService = ref(null)

// the provider text ends with "Read more"; the alert has its own
// "Learn more here" button, so that tail is dropped
const providerInfo = computed(() =>
  String(selectedService.value?.info || '').replace(
    /\s*(Read more|Saiba mais)\.?\s*$/i,
    '',
  ),
)
const fields = computed(() =>
  selectedService.value.custom ? customProviderFields : popularProviderFields,
)

function handleSelect(service) {
  selectedService.value = service
  state.service = service.name
}

const addEmailRes = createResource({
  url: 'crm.api.settings.create_email_account',
  makeParams: (val) => {
    return {
      ...val,
    }
  },
  onSuccess: () => {
    toast.success(__('Email account created successfully'))
    completeStep('connect_your_email')
    emit('update:step', 'email-list')
  },
  onError: (err) => {
    // the server's own reason (e.g. a missing funnel) beats a generic message
    error.value =
      err?.messages?.[0] ||
      __('Failed to create email account: invalid credentials')
  },
})

const error = ref()
function createEmailAccount() {
  error.value = validateInputs(state, selectedService.value.custom)
  if (error.value) return
  if (state.create_lead_from_incoming_email && !state.crm_pipeline) {
    error.value = __('Choose the funnel where cards from emails go.')
    return
  }

  addEmailRes.submit({ data: state })
  capture('email_account_created')
}
</script>

<style scoped>
/* Figma "Caixa de seleção": 20px box (6px radius), 14/20 black label 8px away */
.ct-email-options :deep(input[type='checkbox']) {
  width: 20px;
  height: 20px;
  border-radius: 6px;
}
.ct-email-options :deep(label) {
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  color: var(--ct-text-primary);
}
</style>
