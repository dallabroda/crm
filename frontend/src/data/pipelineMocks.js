// Development-only stand-in for crm.api.pipeline.* (agente Servidor, #67/#69).
// Loaded through a dynamic import guarded by import.meta.env.DEV, so production
// builds never include it. Stage keys reuse the default CRM Deal Status names
// so list/kanban queries keep working against an unmodified backend.
import { call } from 'frappe-ui'

const stage = (name, deal_status, color, type, position, probability) => ({
  name,
  deal_status,
  color,
  type,
  position,
  probability,
})

const pipelines = [
  {
    name: 'mock-vendas',
    pipeline_name: 'Vendas',
    color: 'blue',
    icon: '',
    position: 1,
    is_active: 1,
    my_role: 'Admin',
    stages: [
      stage('Qualification', 'Qualificação', 'gray', 'Open', 1, 10),
      stage('Demo/Making', 'Demonstração', 'orange', 'Ongoing', 2, 25),
      stage('Proposal/Quotation', 'Proposta', 'blue', 'Ongoing', 3, 50),
      stage('Negotiation', 'Negociação', 'yellow', 'Ongoing', 4, 70),
      stage('Ready to Close', 'Pronto para fechar', 'purple', 'Ongoing', 5, 90),
      stage('Won', 'Ganho', 'green', 'Won', 6, 100),
      stage('Lost', 'Perdido', 'red', 'Lost', 7, 0),
    ],
    members: [
      { user: 'Administrator', full_name: 'Administrator', role: 'Owner' },
    ],
    fields: [
      { fieldname: 'organization', position: 1 },
      { fieldname: 'deal_value', position: 2 },
      { fieldname: 'expected_closure_date', position: 3 },
      { fieldname: 'next_step', position: 4 },
    ],
  },
  {
    name: 'mock-credito',
    pipeline_name: 'Crédito',
    color: 'green',
    icon: '',
    position: 2,
    is_active: 1,
    my_role: 'Member',
    stages: [
      stage('Qualification', 'Análise', 'gray', 'Open', 1, 10),
      stage('Negotiation', 'Documentação', 'yellow', 'Ongoing', 2, 60),
      stage('Won', 'Aprovado', 'green', 'Won', 3, 100),
      stage('Lost', 'Recusado', 'red', 'Lost', 4, 0),
    ],
    members: [
      { user: 'Administrator', full_name: 'Administrator', role: 'Member' },
    ],
    fields: [
      { fieldname: 'organization', position: 1 },
      { fieldname: 'deal_value', position: 2 },
      { fieldname: 'next_step', position: 3 },
    ],
  },
]

// Rules worth exercising in the UI: a required field to enter a stage, a hidden
// field and a read-only field.
const rules = {
  'mock-vendas': {
    Negotiation: { next_step: { visible: 1, required: 1, read_only: 0 } },
    Won: { deal_value: { visible: 1, required: 1, read_only: 1 } },
  },
  'mock-credito': {
    Negotiation: {
      expected_closure_date: { visible: 0, required: 0, read_only: 0 },
      next_step: { visible: 1, required: 1, read_only: 0 },
    },
  },
}

const catalog = {
  limit: 80,
  used: 0,
  fields: [
    {
      fieldname: 'organization',
      label: 'Organization',
      fieldtype: 'Link',
      options: 'CRM Organization',
      is_standard: 1,
      locked: 0,
      disabled: 0,
    },
    {
      fieldname: 'deal_value',
      label: 'Deal Value',
      fieldtype: 'Currency',
      options: '',
      is_standard: 1,
      locked: 0,
      disabled: 0,
    },
    {
      fieldname: 'expected_closure_date',
      label: 'Expected Closure Date',
      fieldtype: 'Date',
      options: '',
      is_standard: 1,
      locked: 0,
      disabled: 0,
    },
    {
      fieldname: 'next_step',
      label: 'Next Step',
      fieldtype: 'Data',
      options: '',
      is_standard: 1,
      locked: 0,
      disabled: 0,
    },
    {
      fieldname: 'deal_owner',
      label: 'Deal Owner',
      fieldtype: 'Link',
      options: 'User',
      is_standard: 1,
      locked: 1,
      disabled: 0,
    },
  ],
}

const clone = (value) => JSON.parse(JSON.stringify(value))

function findPipeline(name) {
  return pipelines.find((p) => p.name === name)
}

// Against the real server (only some functions mocked) the funnel key is
// unknown here, so fall back to the Vendas rules: default stage keys match.
function stageRules(pipeline, stageName) {
  let byPipeline = rules[pipeline] || rules['mock-vendas']
  return clone(byPipeline?.[stageName] || {})
}

function fieldRules(pipeline) {
  let p = findPipeline(pipeline)
  if (!p) return []
  let out = []
  for (let s of p.stages) {
    for (let f of p.fields) {
      let r = rules[pipeline]?.[s.name]?.[f.fieldname]
      out.push({
        stage: s.name,
        fieldname: f.fieldname,
        visible: r ? r.visible : 1,
        required: r ? r.required : 0,
        read_only: r ? r.read_only : 0,
      })
    }
  }
  return out
}

// The mock backend has no CRM Deal.pipeline column, so the store tells it which
// funnel the user is looking at (the real API reads it from the card).
let currentPipeline = null
export function setMockPipeline(name) {
  currentPipeline = name
}

async function missingFields(deal, stageName) {
  let pipeline = currentPipeline || pipelines[0].name
  let required = Object.entries(stageRules(pipeline, stageName))
    .filter(([, r]) => r.required)
    .map(([fieldname]) => fieldname)
  if (!required.length) return []
  let doc = await call('frappe.client.get_value', {
    doctype: 'CRM Deal',
    filters: { name: deal },
    fieldname: required,
  })
  return required
    .filter((fieldname) => !doc?.[fieldname])
    .map((fieldname) => {
      let field = catalog.fields.find((f) => f.fieldname === fieldname)
      return {
        fieldname,
        label: field?.label || fieldname,
        fieldtype: field?.fieldtype || 'Data',
        options: field?.options || '',
      }
    })
}

export async function mockCall(method, args = {}) {
  switch (method) {
    case 'get_pipelines':
      return clone(pipelines).map((p) => {
        // get_pipelines does not return members/fields (get_pipeline_config does)
        delete p.members
        delete p.fields
        return p
      })
    case 'get_pipeline_config': {
      let p = findPipeline(args.pipeline)
      return p ? { ...clone(p), field_rules: fieldRules(p.name) } : null
    }
    case 'get_stage_rules':
      return stageRules(args.pipeline, args.stage)
    case 'get_missing_fields':
      return missingFields(args.deal, args.stage)
    case 'move_card': {
      let missing = (await missingFields(args.deal, args.stage)).filter(
        (f) => !args.values?.[f.fieldname],
      )
      if (missing.length) {
        let error = new Error('MissingRequiredFieldsError')
        error.exc_type = 'MissingRequiredFieldsError'
        error.messages = [{ missing_fields: missing }]
        throw error
      }
      return call('frappe.client.set_value', {
        doctype: 'CRM Deal',
        name: args.deal,
        fieldname: { ...(args.values || {}), status: args.stage },
      })
    }
    case 'change_pipeline':
      return call('frappe.client.get', { doctype: 'CRM Deal', name: args.deal })
    case 'save_pipeline': {
      let doc = typeof args.doc === 'string' ? JSON.parse(args.doc) : args.doc
      if (!doc.name) {
        doc.name = 'mock-' + Math.random().toString(36).slice(2, 8)
        pipelines.push({ position: pipelines.length + 1, my_role: 'Owner' })
      }
      let target = findPipeline(doc.name)
      let { field_rules, ...rest } = doc
      Object.assign(target, rest)
      target.stages = (doc.stages || target.stages).map((s, i) => ({
        ...s,
        name:
          s.name ||
          `${doc.name}-stage-${i + 1}-${Math.random().toString(36).slice(2, 6)}`,
        position: i + 1,
      }))
      rules[doc.name] = {}
      for (let r of field_rules || []) {
        rules[doc.name][r.stage] ||= {}
        rules[doc.name][r.stage][r.fieldname] = {
          visible: r.visible,
          required: r.required,
          read_only: r.read_only,
        }
      }
      return mockCall('get_pipeline_config', { pipeline: doc.name })
    }
    case 'get_field_catalog':
      return {
        ...clone(catalog),
        used: catalog.fields.filter((f) => !f.is_standard).length,
      }
    case 'create_field': {
      let field = {
        fieldname: 'custom_' + args.label.toLowerCase().replace(/\W+/g, '_'),
        label: args.label,
        fieldtype: args.fieldtype,
        options: args.options || '',
        is_standard: 0,
        locked: 0,
        disabled: 0,
      }
      catalog.fields.push(field)
      return clone(field)
    }
    case 'update_field':
    case 'disable_field': {
      let field = catalog.fields.find((f) => f.fieldname === args.fieldname)
      if (!field) throw new Error('Field not found')
      if (method === 'disable_field') field.disabled = 1
      if (args.label) field.label = args.label
      if (args.options !== undefined && args.options !== null)
        field.options = args.options
      return clone(field)
    }
    case 'get_pipeline_users': {
      let users = await call('frappe.client.get_list', {
        doctype: 'User',
        filters: { enabled: 1, user_type: 'System User' },
        fields: ['name', 'full_name', 'user_image'],
        limit_page_length: 0,
      })
      return {
        can_create: true,
        is_admin: true,
        users: users
          .filter((u) => u.name !== 'Guest')
          .map((u) => ({
            ...u,
            is_admin: u.name === 'Administrator' ? 1 : 0,
            pipeline_owner: u.name === 'Administrator' ? 1 : 0,
          })),
      }
    }
    case 'set_pipeline_owner_role':
      return { user: args.user, pipeline_owner: args.enabled ? 1 : 0 }
    default:
      throw new Error(`mockCall: unknown method ${method}`)
  }
}
