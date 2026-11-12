// Titles and primary buttons of the create modals: "Nova tarefa" / "Criar
// tarefa" (Figma 2424:26862). Portuguese nouns have a gender ("Novo contato",
// "Nova organização"), so each doctype names its own pair instead of a
// "New {0}" template; the English msgids are translated through __().
const LABELS = {
  'CRM Deal': { title: 'New card', button: 'Create card' },
  'CRM Lead': { title: 'New card', button: 'Create card' },
  Contact: { title: 'New contact', button: 'Create contact' },
  'CRM Organization': {
    title: 'New organization',
    button: 'Create organization',
  },
  'CRM Task': { title: 'New task', button: 'Create task' },
  'FCRM Note': { title: 'New note', button: 'Create note' },
  'CRM Call Log': { title: 'New call log', button: 'Create call log' },
  'CRM Product': { title: 'New product', button: 'Create product' },
  'CRM Industry': { title: 'New industry', button: 'Create industry' },
  'CRM Lead Source': { title: 'New source', button: 'Create source' },
  'CRM Territory': { title: 'New territory', button: 'Create territory' },
  Address: { title: 'New address', button: 'Create address' },
}

// a doctype without a pair: a neutral title, the plain button
const FALLBACK = { title: 'New record', button: 'Create' }

export function createLabels(doctype) {
  const labels = LABELS[doctype] || FALLBACK
  return { title: __(labels.title), button: __(labels.button) }
}
