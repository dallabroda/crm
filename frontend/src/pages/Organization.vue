<template>
  <LayoutHeader v-if="organization.doc">
    <!-- Figma "Organizações · Detalhe" (807:2): "Voltar" + organization name
         on the left; outline actions and the solid primary one on the right -->
    <template #left-header>
      <router-link
        :to="backRoute"
        class="flex h-8 shrink-0 items-center gap-1 rounded-[var(--ct-radius-md)] pl-1 pr-2 text-base font-medium text-ink-gray-6 transition-colors hover:bg-[var(--ct-bg-soft)] hover:text-ink-gray-9 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      >
        <span class="lucide-chevron-left size-4" aria-hidden="true" />
        {{ __('Back') }}
      </router-link>
      <h1
        class="truncate text-[20px] font-semibold leading-7 text-ink-gray-9"
        :title="title"
      >
        {{ title }}
      </h1>
    </template>
    <template #right-header>
      <CustomActions
        v-if="organization._actions?.length"
        :actions="organization._actions"
      />
      <EnrichFromWebsite
        doctype="CRM Organization"
        :docname="props.organizationId"
        :website="organization.doc?.website"
        @done="onEnriched"
      />
      <LocalizeContacts
        :organization="props.organizationId"
        :cnpj="organization.doc?.cnpj"
        @done="onLocalized"
      />
      <Button
        v-if="activeTab === 'deals'"
        variant="solid"
        :label="__('New Deal')"
        iconLeft="lucide-plus"
        @click="showDealModal = true"
      />
      <Link
        v-if="activeTab === 'contacts'"
        value=""
        doctype="Contact"
        :filters="{ company_name: ['!=', props.organizationId] }"
        :onCreate="
          (value, close) => {
            _contact = {
              first_name: value,
              company_name: props.organizationId,
            }
            showContactModal = true
            close()
          }
        "
        @change="(contact) => addContact(contact)"
      >
        <template #target="{ togglePopover }">
          <Button
            variant="solid"
            :label="__('Add Contact')"
            iconLeft="lucide-plus"
            @click="togglePopover()"
          />
        </template>
      </Link>
    </template>
  </LayoutHeader>

  <!-- Banner de Enriquecimento de CNPJ em segundo plano -->
  <div
    v-if="organization.doc?.cnpj && !organization.doc?.cnpj_checked_on"
    class="flex items-center justify-between gap-3 px-6 py-2 bg-[#F5F5F7] border-b border-[#E6E7EB] text-xs text-[#1E1F23]"
  >
    <div class="flex items-center gap-2.5">
      <span class="inline-block size-3.5 animate-spin rounded-full border-2 border-solid border-[#0088FF] border-r-transparent" />
      <span class="font-medium text-[#1E1F23]">
        {{ __('Consultando dados da empresa na Receita Federal...') }}
      </span>
      <span class="text-[#5E6068]">
        {{ __('Identificando razão social, situação cadastral, CNAE, endereço e sócios.') }}
      </span>
    </div>
    <Button
      size="sm"
      variant="ghost"
      :label="__('Atualizar')"
      @click="organization.reload?.()"
    />
  </div>

  <div v-if="organization.doc" ref="parentRef" class="flex h-full">
    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabLabels"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-1 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:gap-4 [&_[role='tablist']]:px-6 [&_[role='tablist']]:border-[var(--ct-border-soft)] [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow [&>[data-slot=tab-list]]:overflow-x-auto [&_[data-slot=tab-indicator]]:translate-y-0 [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-col [&>[data-slot=tab-panel]]:overflow-auto"
    >
      <template #tab-label="{ tab }">{{ __(tab.label) }}</template>
      <template #tab-suffix="{ tab, active }">
        <TabCounter :count="tab.count" :active="active" />
      </template>
      <template #tab-panel="{ tab }">
        <DealsListView
          v-if="tab.label === 'Deals' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <ContactsListView
          v-if="tab.label === 'Contacts' && rows.length"
          class="mt-4"
          :rows="rows"
          :columns="columns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <RecordNotes
          v-if="tab.value === 'notes' && docName"
          :doctype="'CRM Organization'"
          :docname="docName"
          @count="(n) => (notesCount = n)"
        />
        <div
          v-if="tab.value === 'attachments' && docName"
          class="flex flex-col gap-6 p-5"
        >
          <!-- Pasta Digital · Checklist de Documentos & Link Seguro (LGPD) -->
          <CreditOnboardingPanel
            :organization-id="docName"
          />

          <!-- Outros Anexos Gerais / Avulsos -->
          <div class="mt-2 pt-5 border-t border-[#E6E7EB] flex flex-col gap-4">
            <div class="flex items-center justify-between">
              <div>
                <span class="text-base font-semibold text-ink-gray-9">
                  {{ __('Outros Anexos Gerais') }}
                </span>
                <p class="text-xs text-ink-gray-6 mt-0.5">
                  {{ __('Arquivos avulsos anexados diretamente ao cadastro da organização fora do checklist.') }}
                </p>
              </div>
              <Button
                :label="__('Enviar anexo avulso')"
                icon-left="lucide-plus"
                variant="outline"
                @click="showFilesUploader = true"
              />
            </div>
            <AttachmentArea
              v-if="orgAttachments.data?.length"
              :attachments="orgAttachments.data"
              @reload="orgAttachments.reload()"
            />
            <EmptyState
              v-else-if="!orgAttachments.loading"
              :icon="AttachmentIcon"
              :name="__('Anexos')"
              :title="__('Nenhum anexo avulso encontrado')"
              :description="
                __('Use Enviar anexo avulso se precisar guardar arquivos extras que não fazem parte do checklist da pasta digital.')
              "
            />
          </div>
        </div>
        <OrganizationCreditDossie
          v-if="tab.value === 'credit' && docName"
          :organization-id="docName"
          @switch-tab="activeTab = $event"
        />
        <EmptyState
          v-if="
            !['notes', 'credit', 'attachments'].includes(tab.value) &&
            !rows.length
          "
          :icon="tab.iconLeft"
          :name="__(tab.label)"
          :title="
            tab.value === 'deals'
              ? __('No deals found')
              : __('No contacts found')
          "
          :description="
            tab.value === 'deals'
              ? __('Use New Deal to create a deal for this organization.')
              : ''
          "
        />
      </template>
    </Tabs>
    <!-- Figma "Organizações · Detalhe" (807:2): side panel on the right,
         384px, like the card page; actions as 32px outline icon buttons with
         delete last (red) -->
    <Resizer
      v-if="organization.doc"
      side="right"
      :defaultWidth="384"
      class="flex h-full flex-col overflow-hidden border-l border-[var(--ct-border-soft)]"
    >
      <div class="border-b border-[var(--ct-border-soft)]">
        <div class="flex flex-col items-start justify-start gap-4 px-6 py-5">
          <div class="flex w-full min-w-0 items-center gap-4">
            <div class="h-15.5 w-15.5 shrink-0">
              <Avatar
                size="3xl"
                class="h-15.5 w-15.5 [&>div]:text-[20px] [&>div]:font-semibold"
                :label="organization.doc.organization_name"
              />
            </div>
            <div class="flex flex-col gap-2 truncate">
              <div
                class="truncate text-[20px] font-semibold leading-7 text-ink-gray-9"
              >
                <span>{{ organization.doc.name }}</span>
              </div>
              <div
                v-if="organization.doc.website"
                class="flex items-center gap-1.5 text-base text-ink-gray-9"
              >
                <WebsiteIcon class="size-4" />
                <span>{{ website(organization.doc.website) }}</span>
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <Button
              variant="outline"
              :tooltip="__('Open Website')"
              icon="lucide-link-2"
              @click="openWebsite"
            />
            <Button
              variant="outline"
              :tooltip="__('Anexar arquivo')"
              :icon="AttachmentIcon"
              @click="showFilesUploader = true"
            />
            <Button
              v-if="canDelete"
              variant="outline"
              :tooltip="__('Delete')"
              icon="lucide-trash-2"
              class="ct-btn-danger-icon"
              @click="deleteOrganization()"
            />
          </div>
        </div>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="panelSections"
          doctype="CRM Organization"
          :docname="organization.doc.name"
          @reload="sections.reload"
          @beforeFieldChange="beforeFieldChange"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'CRM Organization'"
    :docname="props.organizationId"
    name="Organizations"
  />
  <ContactModal
    v-if="showContactModal"
    v-model="showContactModal"
    :contact="_contact"
    :options="{ redirect: false, afterInsert: () => contacts.reload() }"
  />
  <DealModal
    v-if="showDealModal"
    v-model="showDealModal"
    :defaults="{ organization: props.organizationId }"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="CRM Organization"
    :docname="props.organizationId"
    @after="
      () => {
        orgAttachments.reload()
        activeTab = 'attachments'
      }
    "
  />
</template>

<script setup>
import RecordNotes from '@/components/RecordNotes.vue'
import AttachmentArea from '@/components/Activities/AttachmentArea.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import CreditOnboardingPanel from '@/components/CreditCheck/CreditOnboardingPanel.vue'
import OrganizationCreditDossie from '@/components/CreditCheck/OrganizationCreditDossie.vue'
import FileTextIcon from '~icons/lucide/file-text'
import TabCounter from '@/components/TabCounter.vue'
import MoneyIcon from '@/components/Icons/MoneyIcon.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import ContactsListView from '@/components/ListViews/ContactsListView.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import HandshakeIcon from '~icons/lucide/handshake'
import ContactIcon from '~icons/lucide/contact'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ContactModal from '@/components/Modals/ContactModal.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import Link from '@/components/Controls/Link.vue'
import CustomActions from '@/components/CustomActions.vue'
import EnrichFromWebsite from '@/components/EnrichFromWebsite.vue'
import LocalizeContacts from '@/components/LocalizeContacts.vue'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { getView } from '@/utils/view'
import { globalFormSections } from '@/utils/pipelines'
import {
  validateIsImageFile,
  setupCustomizations,
  openWebsite as openExternalWebsite,
} from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  Avatar,
  FileUploader,
  Dropdown,
  Tabs,
  createListResource,
  usePageMeta,
  createResource,
  toast,
  call,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  organizationId: { type: String, required: true },
})

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { getUser } = usersStore()
const { getDealStatus, getDealStatusLabel } = statusesStore()
const { doctypeMeta } = getMeta('CRM Organization')
const { capture } = useTelemetry()

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const showDeleteLinkedDocModal = ref(false)

const showContactModal = ref(false)
const showDealModal = ref(false)
const _contact = ref({})

const {
  document: organization,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('CRM Organization', props.organizationId)

// Intercepta quando a organização não for encontrada (ex: renomeada pela razão social da Receita)
watch(
  () => organization.error,
  async (err) => {
    if (err) {
      try {
        const res = await call('cred_hub.cnpj.enrich.resolve_organization', {
          org_name: props.organizationId,
        })
        if (res && res.exists && res.name && res.name !== props.organizationId) {
          router.replace({
            name: 'Organization',
            params: { organizationId: res.name },
            query: route.query,
          })
          return
        }
      } catch (e) {
        // fallback
      }
      errorTitle.value = __('Organização não encontrada')
      errorMessage.value = __('A organização "{0}" não foi encontrada.', [
        props.organizationId,
      ])
    }
  },
  { immediate: true },
)

// Polling suave enquanto o CNPJ estiver sendo consultado em segundo plano
let enrichPollInterval = null
watch(
  () => [organization.doc?.cnpj, organization.doc?.cnpj_checked_on],
  ([cnpj, checkedOn]) => {
    if (cnpj && !checkedOn) {
      if (!enrichPollInterval) {
        enrichPollInterval = setInterval(async () => {
          try {
            const res = await call(
              'cred_hub.cnpj.enrich.resolve_organization',
              {
                org_name: props.organizationId,
              },
            )
            if (
              res &&
              res.exists &&
              res.name &&
              res.name !== props.organizationId
            ) {
              clearInterval(enrichPollInterval)
              enrichPollInterval = null
              router.replace({
                name: 'Organization',
                params: { organizationId: res.name },
                query: route.query,
              })
              return
            }
          } catch (e) {}
          organization.reload?.()
        }, 3000)
      }
    } else if (enrichPollInterval) {
      clearInterval(enrichPollInterval)
      enrichPollInterval = null
    }
  },
  { immediate: true },
)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

function onEnriched() {
  organization.reload?.()
  sections.reload()
}

// Assertiva Localize created or updated the partners (credtech#290)
function onLocalized() {
  onEnriched()
  contacts.reload()
}

onMounted(async () => {
  if (organization.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Organizations'), route: { name: 'Organizations' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(
      route.query.view,
      route.query.viewType,
      'CRM Organization',
    )
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Organizations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Organization',
      params: { organizationId: props.organizationId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return organization.doc?.[t] || props.organizationId
})

const backRoute = computed(
  () => breadcrumbs.value[breadcrumbs.value.length - 2].route,
)

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

async function deleteOrganization() {
  showDeleteLinkedDocModal.value = true
}

function changeOrganizationImage(file) {
  organization.setValue.submit({
    organization_logo: file?.file_url || null,
  })
}

function beforeFieldChange(data) {
  if (Object.hasOwn(data ?? {}, 'organization_name')) {
    call('frappe.client.rename_doc', {
      doctype: 'CRM Organization',
      old_name: props.organizationId,
      new_name: data.organization_name,
    }).then(() => {
      router.push({
        name: 'Organization',
        params: { organizationId: data.organization_name },
      })
    })
  } else {
    organization.save.submit()
  }
}

function website(url) {
  return url && url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}

function openWebsite() {
  if (!organization.doc.website) {
    toast.error(__('No Website Found'))
    return
  }

  openExternalWebsite(organization.doc.website)
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Organization'],
  params: { doctype: 'CRM Organization' },
  auto: true,
  transform: (data) => getParsedSections(data),
})

// The company's form of organizations (dynamic forms, credtech#181): its
// fields in its order once saved; created fields show up by themselves
const formSchema = createResource({
  url: 'crm.api.forms.get_form_schema',
  cache: ['formSchema', 'CRM Organization'],
  params: { doctype: 'CRM Organization' },
  auto: true,
})

const panelSections = computed(() => {
  const base = globalFormSections(sections.data, formSchema.data, {
    form: __('Organization fields'),
    created: __('Created fields'),
  })
  // Unify all organization & Receita Federal fields into a single "Campos da organização" section,
  // ensuring all standard and Receita fields are visible and dropping cnpj_checked_on ("CNPJ consultado em")
  const allFieldsMap = new Map()
  for (const sec of sections.data || []) {
    for (const col of sec.columns || []) {
      for (const f of col.fields || []) {
        if (f && typeof f === 'object' && f.fieldname && f.fieldname !== 'cnpj_checked_on') {
          allFieldsMap.set(f.fieldname, { ...f, visible: 1 })
        }
      }
    }
  }
  for (const f of formSchema.data?.fields || []) {
    if (f && f.fieldname && f.fieldname !== 'cnpj_checked_on' && !f.locked) {
      const prev = allFieldsMap.get(f.fieldname) || {}
      allFieldsMap.set(f.fieldname, {
        ...prev,
        ...f,
        visible: 1,
        read_only: f.fieldname === 'years_in_business' ? 1 : 0,
      })
    }
  }
  const preferredOrder = [
    'cnpj',
    'registration_status',
    'activity_start_date',
    'years_in_business',
    'main_cnae',
    'legal_nature',
    'company_size',
    'is_mei',
    'share_capital',
    'annual_revenue',
    'industry',
    'no_of_employees',
    'registry_phone',
    'registry_email',
    'website',
    'linkedin',
    'address',
    'neighborhood',
    'city',
    'state',
  ]
  const ordered = []
  const seen = new Set()
  for (const name of preferredOrder) {
    if (allFieldsMap.has(name)) {
      ordered.push(allFieldsMap.get(name))
      seen.add(name)
    }
  }
  for (const [name, f] of allFieldsMap.entries()) {
    if (!seen.has(name)) {
      ordered.push(f)
      seen.add(name)
    }
  }
  if (!ordered.length) return getParsedSections(base)
  return getParsedSections([
    {
      name: 'form_fields',
      label: __('Campos da organização'),
      opened: true,
      notInLayout: true,
      columns: [{ name: 'form_fields_col', fields: ordered }],
    },
  ])
})

// Returns new objects: panelSections runs it inside a computed, and changing
// sections.data there made the computed run again forever (the page froze)
function getParsedSections(_sections) {
  return _sections.map((section) => ({
    ...section,
    columns: (section.columns || []).map((column) => ({
      ...column,
      fields: (column.fields || []).map((field) => {
        if (field.fieldname === 'address') {
          return {
            ...field,
            create: (value, close) => {
              showAddressModal()
              close()
            },
            edit: (address) => showAddressModal(address),
          }
        } else {
          return field
        }
      }),
    })),
  }))
}

const showFilesUploader = ref(false)
const orgAttachments = createResource({
  url: 'frappe.client.get_list',
  makeParams: () => ({
    doctype: 'File',
    filters: {
      attached_to_doctype: 'CRM Organization',
      attached_to_name: props.organizationId,
    },
    fields: [
      'name',
      'file_name',
      'file_url',
      'file_size',
      'file_type',
      'is_private',
      'creation',
    ],
    order_by: 'creation desc',
    limit_page_length: 0,
  }),
  auto: true,
})

const activeTab = ref('deals')
const tabs = [
  {
    value: 'deals',
    label: 'Deals',
    iconLeft: HandshakeIcon,
    count: computed(() => deals.data?.length),
  },
  {
    value: 'contacts',
    label: 'Contacts',
    iconLeft: ContactIcon,
    count: computed(() => contacts.data?.length),
  },
  // the organization's own comments/notes (credtech#214)
  {
    value: 'notes',
    label: 'Comentários',
    iconLeft: FileTextIcon,
    count: computed(() => notesCount.value),
  },
  {
    value: 'attachments',
    label: 'Anexos',
    iconLeft: AttachmentIcon,
    count: computed(() => orgAttachments.data?.length),
  },
  // credit/legal pre-screening dossier for this organization (credtech#302)
  {
    value: 'credit',
    label: 'Credit Analysis',
    iconLeft: MoneyIcon,
  },
]
const notesCount = ref(0)
const docName = computed(() => organization.doc?.name)

const deals = createListResource({
  type: 'list',
  doctype: 'CRM Deal',
  cache: ['deals', props.organizationId],
  fields: [
    'name',
    'organization',
    'currency',
    'deal_value',
    'status',
    'email',
    'mobile_no',
    'deal_owner',
    'modified',
  ],
  filters: {
    organization: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const contacts = createListResource({
  type: 'list',
  doctype: 'Contact',
  cache: ['contacts', props.organizationId],
  fields: [
    'name',
    'full_name',
    'image',
    'email_id',
    'mobile_no',
    'company_name',
    'modified',
  ],
  filters: {
    company_name: props.organizationId,
  },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const rows = computed(() => {
  let list = activeTab.value === 'deals' ? deals : contacts

  if (!list.data) return []

  return list.data.map((row) => {
    return activeTab.value === 'deals'
      ? getDealRowObject(row)
      : getContactRowObject(row)
  })
})

const { getFormattedCurrency } = getMeta('CRM Deal')

const columns = computed(() => {
  return activeTab.value === 'deals' ? dealColumns : contactColumns
})

function getDealRowObject(deal) {
  return {
    name: deal.name,
    organization: {
      label: deal.organization,
      logo: organization.doc?.organization_logo,
    },
    deal_value: getFormattedCurrency('deal_value', deal),
    status: {
      label: getDealStatusLabel(deal.status),
      color: getDealStatus(deal.status)?.color,
    },
    email: deal.email,
    mobile_no: deal.mobile_no,
    deal_owner: {
      label: deal.deal_owner && getUser(deal.deal_owner).full_name,
      ...(deal.deal_owner && getUser(deal.deal_owner)),
    },
    modified: timestampCell(deal.modified),
  }
}

function getContactRowObject(contact) {
  return {
    name: contact.name,
    full_name: {
      label: contact.full_name,
      image_label: contact.full_name,
      image: contact.image,
    },
    email: contact.email_id,
    mobile_no: contact.mobile_no,
    company_name: {
      label: contact.company_name,
      logo: organization.doc?.organization_logo,
    },
    modified: timestampCell(contact.modified),
  }
}

const dealColumns = [
  {
    label: __('Organization'),
    key: 'organization',
    width: '11rem',
  },
  {
    label: __('Amount'),
    key: 'deal_value',
    align: 'right',
    width: '9rem',
  },
  {
    label: __('Status'),
    key: 'status',
    width: '10rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Mobile Number'),
    key: 'mobile_no',
    width: '11rem',
  },
  {
    label: __('Deal Owner'),
    key: 'deal_owner',
    width: '10rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const contactColumns = [
  {
    label: __('Name'),
    key: 'full_name',
    width: '17rem',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '12rem',
  },
  {
    label: __('Phone'),
    key: 'mobile_no',
    width: '12rem',
  },
  {
    label: __('Organization'),
    key: 'company_name',
    width: '12rem',
  },
  {
    label: __('Last Modified'),
    key: 'modified',
    width: '8rem',
  },
]

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        organization.doc.address = d.name
        organization.save.submit()
      },
    },
  })
}

// Setup custom actions from Form Scripts
watch(
  () => organization.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: organization.setValue.submit,
        deleteDoc: deleteOrganization,
        call,
      })
      organization._actions = s.actions || []
    }
  },
  { once: true },
)

// Figma "Card · Atividades": tab labels without icons (the icons stay in
// `tabs` for the activity empty states)
// Figma "Contatos · Detalhe" / "Organizações · Detalhe": tabs keep their
// 16px icon (the card page's tabs have none)
const tabLabels = computed(() => tabs.value || tabs)
</script>
