<template>
  <!-- Figma "Configurações · WhatsApp" (2324:27125): 48px fields two per row,
       16px apart; "Ativado" in the top bar -->
  <SettingsPage
    doctype="WhatsApp Settings"
    title="WhatsApp"
    :description="
      __(
        'Connect HubTech to the WhatsApp Business API (Meta) to send and receive messages in the cards.',
      )
    "
    header-check="enabled"
    class="ct-field-48 ct-whatsapp-fields"
  />
</template>
<script setup>
import './fieldOutline.css'
import SettingsPage from '@/components/Settings/SettingsPage.vue'
</script>

<style>
.settings-page .ct-whatsapp-fields .column {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  max-width: 1048px;
}
/* Figma "Campo" label: 14/20 Medium Uso/Texto/Secundário, 6px above the box */
.settings-page .ct-whatsapp-fields .field > div:first-child {
  margin-bottom: 6px;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--ct-text-secondary);
}
.settings-page .ct-whatsapp-fields .section:first-child {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}
</style>
