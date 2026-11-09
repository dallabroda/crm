import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

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
  plugins: [],
}
