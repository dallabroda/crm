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
import LucideSettings from '~icons/lucide/settings'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import LucideMonitorCog from '~icons/lucide/monitor-cog'
import LucideStar from '~icons/lucide/star'
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
import LucideHouse from '~icons/lucide/house'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucidePhone from '~icons/lucide/phone'
import LucideKeyRound from '~icons/lucide/key-round'
import LucideSearchCheck from '~icons/lucide/search-check'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'

import ProfilePage from '@/components/Settings/Profile/ProfilePage.vue'
import PreferencesSettings from '@/components/Settings/PreferencesSettings.vue'
import GeneralSettings from '@/components/Settings/GeneralSettings.vue'
import DashboardSettings from '@/components/Settings/DashboardSettings.vue'
import DefaultsSettings from '@/components/Settings/DefaultsSettings.vue'
import BrandSettings from '@/components/Settings/BrandSettings.vue'
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
import HomeActions from '@/components/Settings/HomeActions.vue'
import LeadSyncSourcePage from '@/components/Settings/LeadSyncing/LeadSyncSourcePage.vue'
import TelephonyPage from '@/components/Settings/Telephony/TelephonyPage.vue'
import WhatsAppSettings from '@/components/Settings/WhatsAppSettings.vue'
import ApiKeysPage from '@/components/Settings/ApiKeys/ApiKeysPage.vue'
import BureausSettings from '@/components/Settings/Bureaus/BureausSettings.vue'
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
      key: 'System Configuration',
      condition: () => isManager(),
      items: [
        item('General', LucideSettings, GeneralSettings, {
          title: 'General Settings',
        }),
        item('Dashboard', LucideLayoutDashboard, DashboardSettings),
        item('Defaults', LucideMonitorCog, DefaultsSettings, {
          title: 'System Defaults',
        }),
        item('Brand', LucideStar, BrandSettings, {
          title: 'Brand Settings',
        }),
      ],
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
      key: 'Customization',
      condition: () => isManager(),
      items: [item('Home Actions', LucideHouse, HomeActions)],
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
        item('Cartório & Localização', LucideSearchCheck, BureausSettings, {
          condition: () => isAdmin() && apiKeys.enabled,
        }),
        item(
          'Políticas de Crédito & Compliance',
          LucideShieldCheck,
          CreditBureausSettings,
          { condition: () => isManager() },
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
