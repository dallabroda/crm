import { describe, expect, it } from 'vitest'
import fs from 'fs'
import path from 'path'
import { createLabels } from '@/utils/createLabels'

// msgid -> msgstr of the Portuguese catalog
function poMessages() {
  const po = fs.readFileSync(
    path.resolve(import.meta.dirname, '../../../crm/locale/pt_BR.po'),
    'utf8',
  )
  const out = {}
  for (const m of po.matchAll(/^msgid "(.*)"\nmsgstr "(.*)"$/gm)) out[m[1]] = m[2]
  return out
}

function inPortuguese(doctype) {
  const pt = poMessages()
  const { title, button } = createLabels(doctype)
  return { title: pt[title] || title, button: pt[button] || button }
}

describe('create modal labels', () => {
  it('names the record with its gender and the button in lower case', () => {
    expect(inPortuguese('CRM Task')).toEqual({
      title: 'Nova tarefa',
      button: 'Criar tarefa',
    })
    expect(inPortuguese('Contact')).toEqual({
      title: 'Novo contato',
      button: 'Criar contato',
    })
    expect(inPortuguese('CRM Organization')).toEqual({
      title: 'Nova organização',
      button: 'Criar organização',
    })
    expect(inPortuguese('FCRM Note')).toEqual({
      title: 'Nova anotação',
      button: 'Criar anotação',
    })
    expect(inPortuguese('CRM Deal')).toEqual({
      title: 'Novo card',
      button: 'Criar card',
    })
  })

  it('falls back to a neutral title for an unknown doctype', () => {
    expect(inPortuguese('Some Doctype')).toEqual({
      title: 'Novo registro',
      button: 'Criar',
    })
  })
})
