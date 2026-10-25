// Pure helpers for funnels (pipelines), shared by the Kanban, the card page and tests.

// Fields that are never hidden or locked by stage rules: without them a card
// could not be found, moved or owned (cred-hub-funis.md, "Catálogo de campos").
export const LOCKED_FIELDS = ['pipeline', 'status', 'deal_owner']

// crm.api.pipeline.move_card / CRM Deal save answer a stage with empty
// required fields with MissingRequiredFieldsError carrying
// { missing_fields: [{ fieldname, label, fieldtype, options }] } in a message.
export function missingFieldsFromError(error) {
  if (error?.exc_type !== 'MissingRequiredFieldsError') return null
  let candidates = [...(error.messages || []), error.message, error._server_messages]
  for (let message of candidates) {
    let parsed = parseMaybeJSON(message)
    // _server_messages is a JSON list of JSON strings
    if (Array.isArray(parsed)) {
      for (let item of parsed) {
        let inner = parseMaybeJSON(item)
        inner = parseMaybeJSON(inner?.message) || inner
        if (inner?.missing_fields?.length) return inner.missing_fields
      }
      continue
    }
    if (parsed?.missing_fields?.length) return parsed.missing_fields
  }
  return null
}

function parseMaybeJSON(value) {
  if (typeof value !== 'string') return value
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

// Applies { fieldname: { visible, required, read_only } } (get_stage_rules) to
// side panel sections: hidden fields are dropped, required ones marked reqd and
// read-only ones locked. Returns new sections; the input is not modified.
export function applyStageRules(sections, rules) {
  if (!rules || !Object.keys(rules).length) return sections
  return (sections || []).map((section) => {
    if (!section.columns) return section
    return {
      ...section,
      columns: section.columns.map((column) => ({
        ...column,
        fields: (column.fields || [])
          .map((field) => applyRule(field, rules))
          .filter(Boolean),
      })),
    }
  })
}

function applyRule(field, rules) {
  let name = typeof field === 'string' ? field : field?.fieldname
  let rule = rules[name]
  if (!rule || LOCKED_FIELDS.includes(name)) return field
  if (!rule.visible) return null
  if (typeof field === 'string') return field
  return {
    ...field,
    reqd: rule.required ? 1 : field.reqd,
    read_only: rule.read_only ? 1 : field.read_only,
  }
}
