import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'
import fs from 'node:fs'
import { createRequire } from 'node:module'
import path from 'node:path'
import plugin from 'tailwindcss/plugin'

// Figma icons are 16px with a 1.4px stroke. frappe-ui bakes Lucide's mask
// icons (`lucide-*` classes) at stroke-width 1.5 on a 24px grid, which is
// 1px at 16px. Registering the pack again at 2.1 (= 1.4px at 16px) makes
// these classes come later in the CSS and win. Same CSS as frappe-ui's
// iconPackPlugin (not exported by the package), only the stroke differs.
const lucideIconsDir = path.join(
  path.dirname(
    createRequire(import.meta.url).resolve('lucide-static/package.json'),
  ),
  'icons',
)
const lucideStrokeFigma = plugin(({ matchComponents }) => {
  const values = {}
  for (const file of fs.readdirSync(lucideIconsDir)) {
    if (file.endsWith('.svg')) values[file.slice(0, -4)] = file.slice(0, -4)
  }
  matchComponents(
    {
      lucide: (name) => {
        const file = path.join(lucideIconsDir, `${name}.svg`)
        if (!fs.existsSync(file)) return {}
        const svg = fs
          .readFileSync(file, 'utf8')
          .replace(/stroke-width="[^"]+"/g, 'stroke-width="2.1"')
          .replace(/\s+/g, ' ')
          .trim()
        const uri = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
        return {
          '&:where(:not(svg))': {
            '-webkit-mask-image': `url("${uri}")`,
            'mask-image': `url("${uri}")`,
          },
        }
      },
    },
    { values, type: 'any' },
  )
})

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    ...frappeUIContent,
    // linked @framework/ui source (apps/frappe/ui/src) — scan so its utility and
    // arbitrary-variant classes (e.g. Notifications TabButtons overrides) are generated
    '../../frappe/ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [
    '!text-gray-700',
    '!text-blue-600',
    '!text-green-700',
    '!text-red-600',
    '!text-pink-600',
    '!text-orange-600',
    '!text-amber-600',
    '!text-yellow-600',
    '!text-cyan-600',
    '!text-teal-600',
    '!text-violet-600',
    '!text-purple-600',
    '!text-ink-gray-9',
  ],
  theme: {
    extend: {
      // frappe-ui only ships the numbered radius scale (rounded-0…9), so the
      // named classes used across the app (rounded, rounded-md, rounded-lg…)
      // generated nothing and every box had square corners. Map them to the
      // CredTech Style Guide radii: Raio/Pequeno 6, Médio 8, Grande 12.
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '6px',
        lg: '8px',
        xl: '12px',
        '2xl': '16px',
      },
    },
  },
  plugins: [lucideStrokeFigma],
}
