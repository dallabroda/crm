// Form customization (dynamic forms, credtech#180): the rows of the
// "Configure form" modal, built from crm.api.forms.get_form_schema and sent
// back to crm.api.forms.save_form_config. A flag is 1, 0 or null; null means
// the stages differ ("varies by stage", only when editing all stages) and is
// kept as it is in each stage unless the user changes it.

export const RULE_FLAGS = ['visible', 'required', 'read_only']

export function configRows(schemaFields) {
  return (schemaFields || []).map((f) => {
    let flags = {
      visible: f.visible,
      required: f.required,
      // `read_only` is what the form renders (the field may be read only by
      // itself); the funnel's rule is `read_only_rule`
      read_only: f.read_only_rule ?? f.read_only ?? 0,
    }
    return {
      fieldname: f.fieldname,
      label: f.label,
      fieldtype: f.fieldtype,
      options: f.options,
      locked: Boolean(f.locked),
      is_created: Boolean(f.is_created),
      ...flags,
      original: { ...flags },
    }
  })
}

// Same rules as the server: required or read only implies visible, and a
// hidden field is neither required nor read only
export function setFlag(row, flag, value) {
  if (row.locked) return row
  row[flag] = value ? 1 : 0
  if (flag !== 'visible' && row[flag]) row.visible = 1
  if (flag === 'visible' && !row.visible) {
    row.required = 0
    row.read_only = 0
  }
  return row
}

export function configPayload(rows) {
  return (rows || [])
    .filter((r) => !r.locked)
    .map((r) => ({
      fieldname: r.fieldname,
      visible: r.visible,
      required: r.required,
      read_only: r.read_only,
    }))
}

// Rows whose flag differed between stages and will now be the same in all of
// them: the modal asks before saving
export function equalizedRows(rows) {
  return (rows || []).filter((r) =>
    RULE_FLAGS.some((flag) => r.original?.[flag] == null && r[flag] != null),
  )
}

// Catalog fields the funnel does not use yet (the "use another field" list)
export function unusedFields(catalogFields, rows) {
  let used = new Set((rows || []).map((r) => r.fieldname))
  return (catalogFields || []).filter(
    (f) => !f.disabled && !f.locked && !used.has(f.fieldname),
  )
}

// A catalog field added to the funnel starts visible, optional and editable
// in every stage (crm.api.pipeline sync_rules)
export function newRow(field) {
  let flags = { visible: 1, required: 0, read_only: 0 }
  return {
    fieldname: field.fieldname,
    label: field.label,
    fieldtype: field.fieldtype,
    options: field.options,
    locked: false,
    is_created: !field.is_standard,
    ...flags,
    original: { ...flags },
  }
}
