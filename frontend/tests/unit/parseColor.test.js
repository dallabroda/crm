import { describe, expect, it } from 'vitest'
import { parseColor } from '@/utils'

describe('parseColor', () => {
  it('maps stage colors to the CredTech status tokens (Figma Style Guide)', () => {
    expect(parseColor('gray')).toBe('!text-[color:var(--ct-status-gray)]')
    expect(parseColor('blue')).toBe('!text-[color:var(--ct-status-blue)]')
    expect(parseColor('purple')).toBe('!text-[color:var(--ct-status-purple)]')
    expect(parseColor('violet')).toBe('!text-[color:var(--ct-status-purple)]')
    expect(parseColor('orange')).toBe('!text-[color:var(--ct-status-orange)]')
    expect(parseColor('yellow')).toBe('!text-[color:var(--ct-status-yellow)]')
    expect(parseColor('amber')).toBe('!text-[color:var(--ct-status-yellow)]')
    expect(parseColor('green')).toBe('!text-[color:var(--ct-status-green)]')
    expect(parseColor('red')).toBe('!text-[color:var(--ct-status-red)]')
  })

  it('keeps the Tailwind shade for colors without a status token', () => {
    expect(parseColor('pink')).toBe('!text-pink-600')
    expect(parseColor('cyan')).toBe('!text-cyan-600')
    expect(parseColor('black')).toBe('!text-ink-gray-9')
  })
})
