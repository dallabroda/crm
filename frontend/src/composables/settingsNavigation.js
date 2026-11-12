// Settings are a page (/crm/settings/<slug>), no longer a modal.
//
// The app still opens them the old way in many places
// (`showSettings.value = true`, `activeSettingsPage.value = 'Invite User'`,
// `openSettings(page)` in form scripts). `installSettingsNavigation` turns
// those into a navigation, so every entry point keeps working.
import { watch } from 'vue'
import { showSettings, activeSettingsPage } from '@/composables/settings'

// English label (the value the app uses for `activeSettingsPage`) → URL slug.
// Kept here, without the panels, so the router does not load them up front.
export const SETTINGS_SLUGS = {
  Profile: 'profile',
  Preferences: 'preferences',
  Company: 'company',
  General: 'general',
  Dashboard: 'dashboard',
  Defaults: 'defaults',
  Brand: 'brand',
  Funnels: 'funnels',
  'Form customization': 'form-customization',
  Users: 'users',
  'Invite User': 'invite-user',
  'Users and Plan': 'users-and-plan',
  'Sales Hierarchy': 'sales-hierarchy',
  Accounts: 'email-accounts',
  Templates: 'email-templates',
  'Workflow Automations': 'workflow-automations',
  'Assignment Rules': 'assignment-rules',
  'SLA Policies': 'sla-policies',
  'Lead capture forms': 'lead-capture-forms',
  Enrichment: 'enrichment',
  'Home Actions': 'home-actions',
  'Lead Sources': 'lead-sources',
  Telephony: 'telephony',
  WhatsApp: 'whatsapp',
  API: 'api',
  'Cartório & Localização': 'bureaus',
  'Collection reminders': 'collection-reminders',
  'ERP integration': 'erp-integration',
  'Políticas de Crédito & Compliance': 'credit-compliance',
}

// Slug for a page given as slug, English label or translated label.
export function settingsSlug(page) {
  if (!page) return null
  const slugs = Object.values(SETTINGS_SLUGS)
  if (slugs.includes(page)) return page
  if (SETTINGS_SLUGS[page]) return SETTINGS_SLUGS[page]
  const key = Object.keys(SETTINGS_SLUGS).find((k) => __(k) === page)
  return key ? SETTINGS_SLUGS[key] : null
}

// Sections that now live inside another page: slug → [page, anchor]
// (Figma "Configurações · Empresa" groups the company options on one page)
export const SETTINGS_ALIASES = {
  general: ['company', 'general'],
  brand: ['company', 'brand'],
  defaults: ['company', 'defaults'],
  dashboard: ['company', 'dashboard'],
  'home-actions': ['company', 'home-actions'],
  // Crédito e cobrança has six tabs (designer decision): the Régua de
  // cobrança sits below Cartório & Localização
  'collection-reminders': ['bureaus', 'collection-reminders'],
}

export function settingsRoute(page) {
  const slug = settingsSlug(page)
  const alias = SETTINGS_ALIASES[slug]
  if (alias) {
    return { name: 'Settings', params: { section: alias[0] }, hash: '#' + alias[1] }
  }
  return { name: 'Settings', params: slug ? { section: slug } : {} }
}

export function installSettingsNavigation(router) {
  // Both refs are often set in the same tick, in either order: one watcher
  // sees the final pair.
  watch([showSettings, activeSettingsPage], ([open, page]) => {
    if (!open && !page) return
    // Closing the old modal (`showSettings = false`) means nothing on a page;
    // opening it without a page keeps the current section.
    if (page || router.currentRoute.value.name !== 'Settings') {
      router.push(settingsRoute(page))
    }
    showSettings.value = false
    activeSettingsPage.value = ''
  })
}

// Scrolls the settings content (not the whole app, whose frames hide their
// overflow) to the section with this id: an old link to a merged tab
export function scrollToSettingsSection(id) {
  const el = document.getElementById(id)
  let box = el?.parentElement
  while (box && !/(auto|scroll)/.test(getComputedStyle(box).overflowY)) {
    box = box.parentElement
  }
  if (!el || !box) return
  box.scrollTop +=
    el.getBoundingClientRect().top - box.getBoundingClientRect().top
}
