import { call } from 'frappe-ui'
import { reactive } from 'vue'
import { getRequest } from '../LeadSyncing/metaLeadsApi'

// Users and Plan (credtech#25), served by the cred_hub app: a 14-day trial
// with unlimited users from the company's creation, then 3 plan tiers
// (CRM Vendas, Crédito & Cobrança — Pro, Enterprise) + grandfathering (free_legacy).
const API = 'cred_hub.billing.'

export const PLAN_TIERS = [
  {
    id: 'vendas',
    name: 'CRM Vendas',
    subtitle: 'Funil comercial completo, captação multicanal e WhatsApp',
    basePrice: 119,
    includedUsers: 2,
    extraUserPrice: 49,
    includedOpinions: 0,
    hasCreditAndCollection: false,
    features: [
      '2 usuários incluídos (+ R$ 49/mês por usuário extra)',
      'Funis de vendas ilimitados, Kanban e campos obrigatórios por etapa',
      'Até 60 campos personalizados e 2ª organização vinculada no card',
      'Enriquecimento automático de CNPJ (Receita Federal) e descoberta por domínio de e-mail',
      'Captação automática de leads (formulário no site, Google Ads, Typeform, e-mail e webhooks)',
      'WhatsApp integrado no card/contato, painel lateral SmartChat e telefonia VoIP',
      'Chaves de API e webhooks de saída',
    ],
  },
  {
    id: 'credito_cobranca',
    name: 'Crédito & Cobrança — Pro',
    badge: 'Recomendado',
    subtitle: 'Motor de crédito PJ em 3 níveis, bureaus, dossiê IA e cobrança CENPROT',
    basePrice: 449,
    includedUsers: 5,
    extraUserPrice: 59,
    includedOpinions: 30,
    hasCreditAndCollection: true,
    features: [
      '5 usuários incluídos (+ R$ 59/mês por usuário extra)',
      'Tudo do plano CRM Vendas +',
      '30 Pareceres Executivos de IA por mês incluídos (+ R$ 3,00 por parecer extra)',
      'Esteira de Crédito PJ em 3 níveis (Pré-Triagem Gratuita, Bureaus & Protestos, Compliance & Sócios)',
      'Integração nativa com CGU, PGFN, CNDs, Escavador, DirectD, Quod, Boa Vista, SCR Bacen e Serasa',
      'Dossiê Executivo em PDF, Pasta Digital com link externo (/pasta-credito) e Relatório de Visita',
      'Rating Interno (AA–E) e Mesa de Comitê de Crédito com alçadas e votos',
      'Funil de Cobrança & Aba de Títulos (protesto CENPROT/IEPTB com coobrigados, planilha, promessas e acordos)',
      'Assertiva Localize (localização de sócios e contatos em 1 clique)',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    subtitle: 'Operação em escala com usuários ilimitados e 100 pareceres IA/mês',
    basePrice: 990,
    includedUsers: 1000000,
    unlimitedUsers: true,
    extraUserPrice: 0,
    includedOpinions: 100,
    hasCreditAndCollection: true,
    features: [
      'Usuários ilimitados incluídos (sem custo adicional por assento)',
      'Tudo do plano Crédito & Cobrança — Pro +',
      '100 Pareceres Executivos de IA por mês incluídos (+ R$ 3,00 por parecer extra)',
      'Limites expandidos de requisições na API e webhooks corporativos',
      'Onboarding assistido e suporte prioritário para securitizadoras, FIDCs e factorings',
    ],
  },
]

export const PLAN_COMPARISON_GROUPS = [
  {
    category: 'Assentos e Franquias Mensais',
    rows: [
      { label: 'Mensalidade base', vendas: 'R$ 119/mês', credito_cobranca: 'R$ 449/mês', enterprise: 'R$ 990/mês' },
      { label: 'Usuários incluídos', vendas: '2 usuários', credito_cobranca: '5 usuários', enterprise: 'Ilimitados' },
      { label: 'Usuário adicional', vendas: '+ R$ 49/mês', credito_cobranca: '+ R$ 59/mês', enterprise: 'Incluso (R$ 0)' },
      { label: 'Pareceres Executivos de IA incluídos/mês', vendas: '—', credito_cobranca: '30 / mês', enterprise: '100 / mês' },
    ],
  },
  {
    category: 'CRM Comercial & Produtividade',
    rows: [
      { label: 'Funis de vendas ilimitados, Kanban e listas', vendas: true, credito_cobranca: true, enterprise: true },
      { label: 'Campos obrigatórios por etapa e até 60 campos customizados', vendas: true, credito_cobranca: true, enterprise: true },
      { label: '2ª organização vinculada no card (ex.: sacado / cedente)', vendas: true, credito_cobranca: true, enterprise: true },
      { label: 'Consulta automática de CNPJ (Receita Federal) e domínio de e-mail', vendas: true, credito_cobranca: true, enterprise: true },
      { label: 'Captação automática (Site, Google Ads, Typeform, E-mail e Webhooks)', vendas: true, credito_cobranca: true, enterprise: true },
      { label: 'WhatsApp no card, painel SmartChat e telefonia VoIP', vendas: true, credito_cobranca: true, enterprise: true },
    ],
  },
  {
    category: 'Análise de Crédito PJ & Bureaus',
    rows: [
      { label: 'Esteira de Crédito em 3 níveis (Gratuitas, Bureaus e Sócios)', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Consultas públicas gratuitas (Receita, CGU/CEIS/CNEP, PGFN, CNDs)', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Bureaus pré-pagos (Quod, Boa Vista, SCR Bacen, Serasa, Escavador, CENPROT)', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Dossiê Executivo em PDF + Parecer de Crédito por IA (6 pilares semafóricos)', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Pasta Digital com link externo (/pasta-credito) e Relatório de Visita', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Rating Interno (AA–E), Política dos 5 Cs e Comitê de Crédito com votos', vendas: false, credito_cobranca: true, enterprise: true },
    ],
  },
  {
    category: 'Cobrança, Protesto & Localização',
    rows: [
      { label: 'Funil de Cobrança e Aba de Títulos na Organização', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Protesto nacional CENPROT / IEPTB com coobrigados e importação por planilha', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Controle de baixas, promessas de pagamento e acordos parcelados', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Assertiva Localize (telefones, e-mails e endereços dos sócios em 1 clique)', vendas: false, credito_cobranca: true, enterprise: true },
      { label: 'Rate limits expandidos de API e suporte prioritário', vendas: false, credito_cobranca: false, enterprise: true },
    ],
  },
]

export const planApi = {
  get: () => getRequest(API + 'get_plan'),
  requestExtraUsers: (quantity, payer, planTier = null) =>
    call(API + 'request_extra_users', {
      quantity,
      payer,
      ...(planTier ? { plan_tier: planTier } : {}),
    }),
}

export const plan = reactive({ enabled: false, loading: false, data: null })

export async function loadPlan() {
  plan.loading = true
  try {
    const data = await planApi.get()
    plan.data = data?.enabled ? data : null
    plan.enabled = Boolean(data?.enabled)
  } catch {
    plan.data = null
    plan.enabled = false
  } finally {
    plan.loading = false
  }
}

export function openInvoice(url) {
  window.open(url, '_blank', 'noopener')
}

export function statusBadge(status, inTrial = false) {
  if (inTrial && status === 'Free') {
    return { label: __('Free trial'), theme: 'blue' }
  }
  return (
    {
      Free: { label: __('Free plan'), theme: 'gray' },
      'Awaiting Payment': { label: __('Awaiting payment'), theme: 'orange' },
      Active: { label: __('Active'), theme: 'green' },
      'Past Due': { label: __('Payment overdue'), theme: 'red' },
      Canceled: { label: __('Canceled'), theme: 'gray' },
    }[status] || { label: status, theme: 'gray' }
  )
}

export function inGrace(data, today = localToday()) {
  return Boolean(data?.grace_until && data.grace_until >= today)
}

function localToday() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function usage(data) {
  const used = (data?.used_active || 0) + (data?.used_invited || 0)
  const limit = data?.limit || 0
  const unlimited = Boolean(data?.unlimited || data?.in_trial || limit >= 1000000)
  return { used, limit, unlimited, full: !unlimited && used >= limit }
}

export function dayAfterTrial(data) {
  if (!data?.trial_ends_on) return null
  const [year, month, day] = data.trial_ends_on.split('-').map(Number)
  const next = new Date(year, month - 1, day + 1)
  const pad = (n) => String(n).padStart(2, '0')
  return `${next.getFullYear()}-${pad(next.getMonth() + 1)}-${pad(next.getDate())}`
}

export function getTierSpec(tierId) {
  return PLAN_TIERS.find((t) => t.id === tierId) || null
}

export function chosenTier(data) {
  if (!data) return 'credito_cobranca'
  if (data.pending_plan_tier && getTierSpec(data.pending_plan_tier)) {
    return data.pending_plan_tier
  }
  if (data.plan_tier && getTierSpec(data.plan_tier)) {
    return data.plan_tier
  }
  return 'credito_cobranca'
}

export function describeChange(data, quantity, selectedTier = null) {
  quantity = Math.max(0, parseInt(quantity, 10) || 0)
  const tierSpec = selectedTier ? getTierSpec(selectedTier) : null
  const activeTier = data?.plan_tier || 'free_legacy'
  const activeSpec = getTierSpec(activeTier)

  if (!tierSpec) {
    const monthly = (data?.price_per_user || 0) * quantity
    if (quantity === chosenExtras(data)) return { kind: 'same', monthly }
    if (data?.status !== 'Active') {
      return { kind: quantity ? 'subscribe' : 'free', monthly }
    }
    const paid = data.upgrade ? data.upgrade.paid_extras : data.extras
    if (quantity > paid) return { kind: 'increase', monthly }
    if (quantity < paid)
      return { kind: quantity ? 'decrease' : 'cancel', monthly }
    return { kind: 'keep', monthly }
  }

  const effQty = tierSpec.unlimitedUsers ? 0 : quantity
  const monthly = tierSpec.basePrice + tierSpec.extraUserPrice * effQty
  const currentMonthly =
    data?.status === 'Active'
      ? data.amount ||
        (activeSpec
          ? activeSpec.basePrice + activeSpec.extraUserPrice * (data.extras || 0)
          : (data.price_per_user || 60) * (data.extras || 0))
      : 0

  if (
    data?.status === 'Active' &&
    selectedTier === activeTier &&
    effQty === chosenExtras(data)
  ) {
    return { kind: 'same', monthly }
  }
  if (
    data?.status === 'Awaiting Payment' &&
    selectedTier === (data.pending_plan_tier || activeTier) &&
    effQty === chosenExtras(data)
  ) {
    return { kind: 'same', monthly }
  }
  if (data?.status !== 'Active') {
    return { kind: monthly > 0 ? 'subscribe' : 'free', monthly }
  }
  if (monthly > currentMonthly) return { kind: 'increase', monthly }
  if (monthly < currentMonthly)
    return { kind: monthly > 0 ? 'decrease' : 'cancel', monthly }
  return { kind: 'keep', monthly }
}

export function chosenExtras(data) {
  if (!data) return 0
  if (data.status === 'Active') {
    return data.scheduled_extras ?? data.upgrade?.extras ?? data.extras ?? 0
  }
  if (data.status === 'Awaiting Payment') return data.pending_extras || 0
  return data.status === 'Past Due' ? data.extras || 0 : 0
}

export function overLimitAfter(data, quantity, selectedTier = null) {
  const tierSpec = selectedTier ? getTierSpec(selectedTier) : null
  if (tierSpec?.unlimitedUsers) return 0
  const included = tierSpec ? tierSpec.includedUsers : data?.free || 0
  const limit = included + Math.max(0, parseInt(quantity, 10) || 0)
  return Math.max(0, (data?.used_active || 0) - limit)
}
