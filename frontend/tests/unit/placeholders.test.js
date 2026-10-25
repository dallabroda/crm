import { describe, expect, it } from 'vitest'
import { translatePlaceholder } from '@/utils/placeholders'

const pt = {
  'Add {0}...': 'Adicionar {0}...',
  'Select {0}...': 'Selecione {0}...',
  Industry: 'Setor de Atuação',
  'Deal Owner': 'Responsável',
  'Type a CNPJ': 'Digite um CNPJ',
}
const t = (m, args = []) =>
  (pt[m] || m).replace(/\{(\d+)\}/g, (_, i) => args[Number(i)])

describe('translatePlaceholder', () => {
  it('rebuilds the server default from the translated label', () => {
    expect(translatePlaceholder('Add Industry...', 'Industry', t)).toBe(
      'Adicionar Setor de Atuação...',
    )
    expect(translatePlaceholder('Select Deal Owner...', 'Deal Owner', t)).toBe(
      'Selecione Responsável...',
    )
  })

  it('translates a custom placeholder as a whole', () => {
    expect(translatePlaceholder('Type a CNPJ', 'CNPJ', t)).toBe(
      'Digite um CNPJ',
    )
  })

  it('leaves a custom text that only looks like a default alone', () => {
    expect(translatePlaceholder('Add notes...', 'Industry', t)).toBe(
      'Add notes...',
    )
  })

  it('handles an empty placeholder', () => {
    expect(translatePlaceholder('', 'Industry', t)).toBe('')
  })
})
