// Field types of the pipeline field catalog, in the user's words. The labels are translated when
// called (not at import), so they follow the user's language.

// What a link field points to (never the internal doctype name)
const linkTargets = () => ({
  Contact: __('Contact'),
  'CRM Organization': __('Organization'),
  'CRM Pipeline': __('Pipeline'),
  'CRM Deal Status': __('Status'),
  User: __('User'),
  'CRM Lead Source': __('Source'),
  'CRM Industry': __('Industry'),
  'CRM Territory': __('Territory'),
  'CRM Lost Reason': __('Lost Reason'),
  'CRM Lead': __('Lead'),
})

// Types a company can create (cred-hub-funis.md, "Tipos de campo")
export const fieldTypeOptions = () => [
  { label: __('Text'), value: 'Data' },
  { label: __('Number'), value: 'Int' },
  { label: __('Decimal number'), value: 'Float' },
  { label: __('Amount (R$)'), value: 'Currency' },
  { label: __('Date'), value: 'Date' },
  { label: __('List of options'), value: 'Select' },
  { label: __('Yes/No'), value: 'Check' },
  { label: __('File'), value: 'Attach' },
  { label: __('Link to contact or organization'), value: 'Link' },
]

// Types used only by standard fields or by other apps, so they are not offered in "New field"
const otherTypes = () => ({
  Datetime: __('Date and time'),
  'Small Text': __('Long text'),
  Text: __('Long text'),
  'Long Text': __('Long text'),
  'Text Editor': __('Long text'),
  Percent: __('Percentage'),
  Duration: __('Duration'),
  Phone: __('Phone'),
  'Attach Image': __('Image'),
  'Dynamic Link': __('Linked record'),
})

export function fieldTypeLabel(field) {
  // "Linked record", not "Link": in Portuguese "Ligação" reads as a phone call, and the HubTech has telephony
  if (field.fieldtype === 'Link') {
    let target =
      linkTargets()[field.options] || (field.options && __(field.options))
    return target ? `${__('Linked record')}: ${target}` : __('Linked record')
  }
  return (
    fieldTypeOptions().find((o) => o.value === field.fieldtype)?.label ||
    otherTypes()[field.fieldtype] ||
    field.fieldtype
  )
}
