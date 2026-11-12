// Sections of the Settings page (/crm/settings/<slug>), grouped as in the
// settings sidebar. Moved from the old Settings modal: same items, same
// conditions; each item now has a URL slug.
//
// - `key`: the English label, the value the app sets in `activeSettingsPage`
//   (and `openSettings(page)`) to deep-link a section. The translated label is
//   accepted too.
// - `title`: what the top bar shows when the panel does not set its own title.
import { markRaw } from 'vue'
import LucideUserRound from '~icons/lucide/user-round'
import LucideSlidersVertical from '~icons/lucide/sliders-vertical'
import LucideKanban from '~icons/lucide/kanban'
import LucideTextCursorInput from '~icons/lucide/text-cursor-input'
import LucideUser from '~icons/lucide/user'
import LucideUserPlus from '~icons/lucide/user-plus'
import LucideCreditCard from '~icons/lucide/credit-card'
import LucideNetwork from '~icons/lucide/network'
import LucideMail from '~icons/lucide/mail'
import LucideBuilding2 from '~icons/lucide/building-2'
import LucideWorkflow from '~icons/lucide/workflow'
import LucideGitBranch from '~icons/lucide/git-branch'
import LucideShieldCheck from '~icons/lucide/shield-check'
import LucideZap from '~icons/lucide/zap'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucidePhone from '~icons/lucide/phone'
import LucideKeyRound from '~icons/lucide/key-round'
import LucideSearchCheck from '~icons/lucide/search-check'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideUsers from '~icons/lucide/users'
import LucideMessageCircle from '~icons/lucide/message-circle'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'

import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import CompanySettings from '@/components/Settings/CompanySettings.vue'
import PipelinesPage from '@/components/Settings/Pipelines/PipelinesPage.vue'
import FormCustomizationPage from '@/components/Settings/FormCustomization/FormCustomizationPage.vue'
import Users from '@/components/Settings/Users.vue'
import InviteUserPage from '@/components/Settings/InviteUserPage.vue'
import UsersAndPlan from '@/components/Settings/UsersAndPlan/UsersAndPlan.vue'
import Hierarchy from '@/components/Settings/Hierarchy/Hierarchy.vue'
import EmailConfig from '@/components/Settings/EmailConfig.vue'
import EmailTemplatePage from '@/components/Settings/EmailTemplate/EmailTemplatePage.vue'
import WorkflowAutomationPage from '@/components/Settings/WorkflowAutomations/WorkflowAutomationPage.vue'
import AssignmentRulePage from '@/components/Settings/AssignmentRules/AssignmentRulePage.vue'
import SlaConfig from '@/components/Settings/Sla/SlaConfig.vue'
import FormsSettings from '@/components/Settings/Forms/FormsSettings.vue'
import EnrichmentSettings from '@/components/Settings/Enrichment/EnrichmentSettings.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ApiKeysPage from '@/components/Settings/ApiKeys/ApiKeysPage.vue'
import BureausSettings from '@/components/Settings/Bureaus/BureausSettings.vue'
import ErpSettings from '@/components/Settings/Erp/ErpSettings.vue'
import CreditBureausSettings from '@/components/Settings/CreditBureaus/CreditBureausSettings.vue'

import { plan } from '@/components/Settings/UsersAndPlan/planApi'
import { apiKeys } from '@/components/Settings/ApiKeys/apiKeysApi'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import { usersStore } from '@/stores/users'
import { SETTINGS_SLUGS } from '@/composables/settingsNavigation'

function item(key, icon, component, extra = {}) {
  return {
    slug: SETTINGS_SLUGS[key],
    key,
    icon: markRaw(icon),
    component: markRaw(component),
    ...extra,
  }
}

// Full list, before conditions. Labels stay as English keys here and are
// translated when the list is built, so a language change is picked up.
function allSections() {
  const { isAdmin, isManager } = usersStore()
  return [
    {
      key: 'User Configuration',
      items: [
        item('Profile', LucideUserRound, ProfilePage),
        item('Preferences', LucideSlidersVertical, PreferencesSettings),
      ],
    },
    {
      // Figma "Configurações · Empresa": Geral, Marca, Valores padrão, Painel
      // and Ações da página inicial on one page (CompanySettings)
      key: 'Empresa',
      condition: () => isManager(),
      items: [item('Company', LucideBuilding2, CompanySettings, { title: 'Empresa' })],
    },
    {
      key: 'Funnels',
      items: [
        item('Funnels', LucideKanban, PipelinesPage),
        // fields of the cards and their form per funnel and stage (credtech#180);
        // funnel owners configure their funnels, others see the preview
        item(
          'Form customization',
          LucideTextCursorInput,
          FormCustomizationPage,
        ),
      ],
    },
    {
      key: 'User Management',
      condition: () => isManager(),
      items: [
        item('Users', LucideUser, Users, {
          condition: () => isManager(),
        }),
        item('Invite User', LucideUserPlus, InviteUserPage, {
          title: 'Invite users',
          condition: () => isManager(),
        }),
        item(
          'Users and Plan',
          LucideCreditCard,
          UsersAndPlan,
          // only while extra-user billing is on (credhub_billing)
          { condition: () => isAdmin() && plan.enabled },
        ),
        item('Sales Hierarchy', LucideNetwork, Hierarchy, {
          condition: () => isManager(),
        }),
      ],
    },
    {
      key: 'Email',
      items: [
        item('Accounts', LucideMail, EmailConfig, {
          title: 'Email Accounts',
          condition: () => isManager(),
        }),
        item('Templates', LucideBuilding2, EmailTemplatePage, {
          title: 'Email Templates',
        }),
      ],
    },
    {
      key: 'Automation & Rules',
      condition: () => isManager(),
      items: [
        item('Workflow Automations', LucideWorkflow, WorkflowAutomationPage, {
          condition: () => window.has_automation_engine,
        }),
        item('Assignment Rules', LucideGitBranch, AssignmentRulePage),
        item('SLA Policies', LucideShieldCheck, SlaConfig),
        item('Lead capture forms', LucideTextCursorInput, FormsSettings),
        item('Enrichment', LucideZap, EnrichmentSettings, {
          title: 'Enrichment Settings',
          condition: () => false,
        }),
      ],
    },
    {
      key: 'Integrations',
      context: 'FCRM',
      items: [
        item('Lead Sources', LucideMegaphone, LeadSyncSourcePage, {
          condition: () => isManager(),
        }),
        item('Telephony', LucidePhone, TelephonyPage, {
          title: 'Telephony Settings',
        }),
        item('WhatsApp', WhatsAppIcon, WhatsAppSettings, {
          condition: () => isWhatsappInstalled.value && isManager(),
        }),
        // admins only, with the cred_hub app (credtech#175)
        item('API', LucideKeyRound, ApiKeysPage, {
          condition: () => isAdmin() && apiKeys.enabled,
        }),
        // Assertiva Localize and CENPROT (credtech#290): admins only, with the cred_hub app
        // with the Régua de cobrança (credtech#367) below: tab "Cartório e
        // cobrança"; /settings/collection-reminders lands there
        item('Cartório & Localização', LucideSearchCheck, BureausSettings, {
          title: 'Crédito e cobrança',
          condition: () => isAdmin() && apiKeys.enabled,
        }),
        // WBA / Smart Securities (credtech#367): admins only, with the cred_hub app
        item('ERP integration', LucideArrowLeftRight, ErpSettings, {
          title: 'Crédito e cobrança',
          condition: () => isAdmin() && apiKeys.enabled,
        }),
        item(
          'Políticas de Crédito & Compliance',
          LucideShieldCheck,
          CreditBureausSettings,
          { title: 'Crédito e cobrança', condition: () => isManager() },
        ),
      ],
    },
  ]
}

// Sections and items the current user can see, with translated labels.
export function getSettingsSections() {
  return allSections()
    .filter((section) => !section.condition || section.condition())
    .map((section) => ({
      ...section,
      label: __(section.key, null, section.context || null),
      items: section.items
        .filter((i) => !i.condition || i.condition())
        .map((i) => ({
          ...i,
          label: __(i.key),
          title: __(i.title || i.key),
        })),
    }))
    .filter((section) => section.items.length)
}

// Finds an item by slug, English key or translated label.
export function findSettingsItem(sections, page) {
  if (!page) return null
  const items = sections.flatMap((section) => section.items)
  return (
    items.find((i) => i.slug === page) ||
    items.find((i) => i.key === page) ||
    items.find((i) => i.label === page) ||
    null
  )
}

// Figma "Barra lateral secundária · Configurações" (Configurações · Empresa
// 2323:14221): three groups and eleven entries. An entry stands for one or
// more sections that have tabs between them (Equipe → Pessoas / Hierarquia,
// Crédito e cobrança → its tabs); no sub-items, to keep the menu short.
// Sections in no entry (Perfil, Preferências → "Minha conta") stay reachable
// by URL.
const NAV = [
  {
    key: 'Empresa',
    entries: [
      { key: 'Empresa', icon: LucideBuilding2, slugs: ['company'] },
      { key: 'Equipe', icon: LucideUsers,
        slugs: ['users', 'invite-user', 'sales-hierarchy'] },
      { key: 'Plano e cobrança', icon: LucideCreditCard,
        slugs: ['users-and-plan'] },
    ],
  },
  {
    key: 'Vendas e crédito',
    entries: [
      { key: 'Funis', icon: LucideKanban,
        slugs: ['funnels', 'form-customization'] },
      { key: 'Automação', icon: LucideWorkflow,
        slugs: ['workflow-automations', 'assignment-rules', 'sla-policies'] },
      { key: 'Crédito e cobrança', icon: LucideShieldCheck,
        slugs: ['credit-compliance', 'bureaus', 'erp-integration'] },
    ],
  },
  {
    key: 'Canais e integrações',
    entries: [
      { key: 'E-mail', icon: LucideMail,
        slugs: ['email-accounts', 'email-templates'] },
      { key: 'WhatsApp', icon: LucideMessageCircle, slugs: ['whatsapp'] },
      { key: 'Telefonia', icon: LucidePhone, slugs: ['telephony'] },
      { key: 'Entrada de leads', icon: LucideMegaphone,
        slugs: ['lead-sources', 'lead-capture-forms'] },
      { key: 'API', icon: LucideKeyRound, slugs: ['api'] },
    ],
  },
]

// The sidebar groups for the sections the user can see (see NAV). Each entry
// opens its first visible section and is active on any of its sections.
export function getSettingsNav(sections) {
  const bySlug = new Map(
    sections.flatMap((section) => section.items).map((i) => [i.slug, i]),
  )
  return NAV.map((group) => ({
    key: group.key,
    label: __(group.key),
    entries: group.entries
      .map((entry) => {
        const items = entry.slugs.map((s) => bySlug.get(s)).filter(Boolean)
        if (!items.length) return null
        return {
          key: entry.key,
          label: __(entry.key),
          icon: markRaw(entry.icon),
          slugs: items.map((i) => i.slug),
          target: items[0].slug,
        }
      })
      .filter(Boolean),
  })).filter((group) => group.entries.length)
}
