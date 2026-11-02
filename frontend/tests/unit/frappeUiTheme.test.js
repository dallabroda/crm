import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import credtechFrappeUiTheme, {
  applyPatches,
  patches,
} from '../../src/theme/frappeUiTheme.js'

const frappeUiSrc = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../node_modules/frappe-ui/src',
)

describe('credtech frappe-ui theme', () => {
  it.each(Object.keys(patches))(
    'applies every patch to the installed %s',
    (file) => {
      const source = fs.readFileSync(path.join(frappeUiSrc, file), 'utf8')
      const out = applyPatches(source, patches[file], file)
      for (const [, to] of patches[file]) expect(out).toContain(to)
    },
  )

  it('fails loudly when a class string is missing', () => {
    expect(() =>
      applyPatches('nothing here', [['missing', 'x']], 'X.vue'),
    ).toThrow(/expected 1 match, found 0/)
  })

  it('only touches frappe-ui source modules, not Vue sub-requests', () => {
    const plugin = credtechFrappeUiTheme()
    expect(plugin.transform('a', '/app/src/Button.vue')).toBeNull()
    expect(
      plugin.transform(
        'a',
        '/x/node_modules/frappe-ui/src/components/Button/Button.vue?vue&type=style',
      ),
    ).toBeNull()
  })

  it('adds the name-based avatar tones', () => {
    const source = fs.readFileSync(
      path.join(frappeUiSrc, 'components/Avatar/Avatar.vue'),
      'utf8',
    )
    const out = applyPatches(
      source,
      patches['components/Avatar/Avatar.vue'],
      'Avatar',
    )
    expect(out).toContain("props.theme === 'gray'")
    expect(out).toContain('--ct-avatar-cyan-bg')
  })
})
