<template>
  <section class="flex flex-col gap-3" data-testid="email-company-setting">
    <div class="flex items-start justify-between gap-4">
      <div class="flex flex-col gap-1">
        <h3 class="text-lg-semibold text-ink-gray-8">
          {{ __("Find the company from the lead's e-mail") }}
        </h3>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'With a company e-mail (not Gmail, Hotmail...), HubTech looks up who owns the domain at Registro.br and checks the CNPJ at the Receita. Sure match: the card gets the organization. Probable match: the card shows it for you to confirm.',
            )
          }}
        </p>
      </div>
      <Switch
        :model-value="Boolean(setting.data?.enabled)"
        :disabled="setting.loading || saving"
        @update:model-value="save"
      />
    </div>
  </section>
</template>

<script setup>
// Company from the lead's e-mail domain (credtech#187): on by default
import { Switch, call, createResource, toast } from 'frappe-ui'
import { ref } from 'vue'

const setting = createResource({
  url: 'cred_hub.email_company.apply.get_setting',
  method: 'GET',
  auto: true,
})
const saving = ref(false)

async function save(value) {
  saving.value = true
  try {
    setting.data = await call('cred_hub.email_company.apply.save_setting', {
      enabled: value ? 1 : 0,
    })
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Could not save the setting'))
  } finally {
    saving.value = false
  }
}
</script>
