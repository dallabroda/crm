/**
 * CredTech visual theme for frappe-ui components (Vite plugin).
 *
 * frappe-ui ships its .vue sources and the app compiles them (it is excluded
 * from pre-bundling in vite.config.js). Most of the CredTech look comes from the
 * tokens in ./credtech.css. Some components, though, hard-code colors and shapes
 * that no token reaches (the solid button is near-black, the tooltip and the
 * switch share that same "gray-10" surface, the toast is dark). This plugin
 * swaps those class strings for the CredTech ones when Vite loads the
 * component, before Vue compiles it.
 *
 * Rules:
 * - Only class strings change. Props, events and behavior stay exactly as in
 *   frappe-ui 1.0.0-rc.2 (pinned in package.json; the fork no longer updates it).
 * - Every `from` must match the source exactly once. If frappe-ui ever changes,
 *   the build fails here instead of silently shipping the old look.
 * - Classes live in this file (inside src/) so Tailwind's content scan
 *   generates them.
 *
 * Figma: "CredTech Digital" → Style Guide (node 550:1162).
 */

const AVATAR_TONES = `[
    'bg-[var(--ct-avatar-green-bg)] text-[color:var(--ct-avatar-green-fg)]',
    'bg-[var(--ct-avatar-orange-bg)] text-[color:var(--ct-avatar-orange-fg)]',
    'bg-[var(--ct-avatar-yellow-bg)] text-[color:var(--ct-avatar-yellow-fg)]',
    'bg-[var(--ct-avatar-blue-bg)] text-[color:var(--ct-avatar-blue-fg)]',
    'bg-[var(--ct-avatar-purple-bg)] text-[color:var(--ct-avatar-purple-fg)]',
    'bg-[var(--ct-avatar-pink-bg)] text-[color:var(--ct-avatar-pink-fg)]',
    'bg-[var(--ct-avatar-cyan-bg)] text-[color:var(--ct-avatar-cyan-fg)]',
  ]`

export const patches = {
  // Figma "Botão" (939:386) and "Botão de ícone" (959:135).
  // solid gray/blue → Destaque (blue), solid red → Destrutivo,
  // subtle gray → Sutil, subtle red → Destrutivo suave,
  // outline gray → Contorno cinza, ghost → Fantasma. Radius 6px.
  'components/Button/Button.vue': [
    [
      `gray: 'text-ink-base bg-surface-gray-10 hover:bg-surface-gray-9 active:bg-surface-gray-8',
        blue: 'text-ink-base bg-surface-blue-6 hover:bg-surface-blue-7 active:bg-surface-blue-8',`,
      `gray: 'font-semibold text-white bg-[var(--ct-accent)] hover:bg-[var(--ct-accent-hover)] active:bg-[var(--ct-accent-active)]',
        blue: 'font-semibold text-white bg-[var(--ct-accent)] hover:bg-[var(--ct-accent-hover)] active:bg-[var(--ct-accent-active)]',`,
    ],
    [
      `red: 'text-ink-base dark:text-ink-red-9 bg-surface-red-7 hover:bg-surface-red-8 active:bg-surface-red-9',`,
      `red: 'font-semibold text-white bg-[var(--ct-danger)] hover:bg-[var(--ct-danger-hover)] active:bg-[var(--ct-danger-hover)]',`,
    ],
    [
      `gray: 'text-ink-gray-8 bg-surface-gray-2 hover:bg-surface-gray-3 active:bg-surface-gray-4',
        blue: 'text-ink-blue-5 bg-surface-blue-2 hover:bg-surface-blue-3 active:bg-surface-blue-4',`,
      `gray: 'font-semibold text-[color:var(--ct-text-primary)] bg-[var(--ct-action-neutral)] hover:bg-[var(--ct-action-neutral-hover)] active:bg-[var(--ct-action-neutral-hover)]',
        blue: 'font-semibold text-[color:var(--ct-accent-text)] bg-[var(--ct-accent-soft)] hover:bg-[var(--ct-accent-soft-hover)] active:bg-[var(--ct-accent-soft-hover)]',`,
    ],
    [
      `red: 'text-ink-red-7 bg-surface-red-2 hover:bg-surface-red-3 active:bg-surface-red-4',`,
      `red: 'font-semibold text-[color:var(--ct-danger)] bg-[var(--ct-danger-soft)] hover:bg-[var(--ct-danger-soft-hover)] active:bg-[var(--ct-danger-soft-hover)]',`,
    ],
    [
      `gray: 'text-ink-gray-8 bg-surface-base border border-outline-gray-2 hover:border-outline-gray-3 active:border-outline-gray-3 active:bg-surface-gray-4',
        blue: 'text-ink-blue-5 bg-surface-base border border-outline-blue-1 hover:border-outline-blue-4 active:border-outline-blue-4 active:bg-surface-blue-4',`,
      `gray: 'font-medium text-[color:var(--ct-text-primary)] bg-[var(--ct-bg-page)] border border-[var(--ct-border)] hover:bg-[var(--ct-bg-soft)] active:bg-[var(--ct-bg-panel)]',
        blue: 'font-medium text-[color:var(--ct-accent-text)] bg-[var(--ct-bg-page)] border border-[var(--ct-accent)] hover:bg-[var(--ct-accent-soft)] active:bg-[var(--ct-accent-soft-hover)]',`,
    ],
    [
      `red: 'text-ink-red-7 bg-surface-base border border-outline-red-1 hover:border-outline-red-3 active:border-outline-red-3 active:bg-surface-red-3',`,
      `red: 'font-medium text-[color:var(--ct-danger)] bg-[var(--ct-bg-page)] border border-[var(--ct-danger)] hover:bg-[var(--ct-danger-soft)] active:bg-[var(--ct-danger-soft-hover)]',`,
    ],
    [
      `gray: 'text-ink-gray-8 bg-transparent hover:bg-surface-gray-3 active:bg-surface-gray-4',
        blue: 'text-ink-blue-5 bg-transparent hover:bg-surface-blue-3 active:bg-surface-blue-4',`,
      `gray: 'font-medium text-[color:var(--ct-text-primary)] bg-transparent hover:bg-[var(--ct-bg-soft)] active:bg-[var(--ct-bg-panel)]',
        blue: 'font-medium text-[color:var(--ct-accent-text)] bg-transparent hover:bg-[var(--ct-accent-soft)] active:bg-[var(--ct-accent-soft-hover)]',`,
    ],
    [
      `red: 'text-ink-red-7 bg-transparent hover:bg-surface-red-3 active:bg-surface-red-4',`,
      `red: 'font-medium text-[color:var(--ct-danger)] bg-transparent hover:bg-[var(--ct-danger-soft)] active:bg-[var(--ct-danger-soft-hover)]',`,
    ],
    // Disabled: same look as the variant, faded (Figma "Desativado").
    [
      `const stateClasses = props.disabled
        ? disabledClasses`,
      `const stateClasses = props.disabled
        ? [variantClasses, 'opacity-50 cursor-not-allowed']`,
    ],
    // Pressed / menu open (Figma "Filtro" → Aberto: black border).
    [
      `'gray-solid': 'text-ink-base bg-surface-gray-8',
        'gray-subtle': 'text-ink-gray-8 bg-surface-gray-4',
        'gray-outline':
          'text-ink-gray-8 bg-surface-gray-4 border border-outline-gray-3',
        'gray-ghost': 'text-ink-gray-8 bg-surface-gray-4',

        'blue-solid': 'text-ink-base bg-surface-blue-8',`,
      `'gray-solid': 'font-semibold text-white bg-[var(--ct-accent-active)]',
        'gray-subtle': 'font-semibold text-[color:var(--ct-text-primary)] bg-[var(--ct-bg-panel)]',
        'gray-outline':
          'font-medium text-[color:var(--ct-text-primary)] bg-[var(--ct-bg-page)] border border-[var(--ct-border-strong)]',
        'gray-ghost': 'font-medium text-[color:var(--ct-text-primary)] bg-[var(--ct-bg-panel)]',

        'blue-solid': 'font-semibold text-white bg-[var(--ct-accent-active)]',`,
    ],
    [
      `'red-solid': 'text-ink-base bg-surface-red-9',`,
      `'red-solid': 'font-semibold text-white bg-[var(--ct-danger-hover)]',`,
    ],
    [
      `'inline-flex items-center justify-center gap-2 transition-colors shrink-0',`,
      `'inline-flex items-center justify-center gap-1.5 transition-colors shrink-0',`,
    ],
    [
      `xs: 'h-6 w-6 rounded-3',
            sm: 'h-7 w-7 rounded-4',
            md: 'h-8 w-8 rounded-4',
            lg: 'h-10 w-10 rounded-5',`,
      `xs: 'h-6 w-6 rounded-[var(--ct-radius-sm)]',
            sm: 'h-7 w-7 rounded-[var(--ct-radius-sm)]',
            md: 'h-8 w-8 rounded-[var(--ct-radius-sm)]',
            lg: 'h-10 w-10 rounded-[var(--ct-radius-sm)]',`,
    ],
    // Heights stay 24/28/32/40 so no screen reflows; padding and type follow
    // Figma (32 → 16px, 40 → 24px, 14px label).
    [
      `xs: 'h-6 text-xs px-1.5 rounded-3',
            sm: 'h-7 text-base px-2 rounded-4',
            md: 'h-8 text-base-medium px-2.5 rounded-4',
            lg: 'h-10 text-lg-medium px-3 rounded-5',`,
      `xs: 'h-6 text-xs px-2 rounded-[var(--ct-radius-sm)]',
            sm: 'h-7 text-base px-2.5 rounded-[var(--ct-radius-sm)]',
            md: 'h-8 text-base px-4 rounded-[var(--ct-radius-sm)]',
            lg: 'h-10 text-base px-6 rounded-[var(--ct-radius-sm)]',`,
    ],
  ],

  // Figma "Campo" (940:99) for outline inputs and "Campo de busca"
  // (1143:28339) for subtle ones: gray fill, white + blue border on focus.
  'components/TextInput/TextInput.vue': inputPatches(),
  'components/Textarea/Textarea.vue': inputPatches(),
  // Figma "Filtro" (1165:20747): open state gets the strong border.
  'components/Select/utils.ts': [
    [
      `'border border-[--surface-gray-2] bg-surface-gray-2 hover:border-outline-elevation-2 hover:bg-surface-gray-3',`,
      `'border border-[--surface-gray-2] bg-surface-gray-2 hover:border-outline-elevation-2 hover:bg-surface-gray-3 data-[state=open]:bg-surface-base data-[state=open]:border-[var(--ct-accent)]',`,
    ],
    [
      `'border border-outline-gray-2 bg-surface-base hover:border-outline-gray-3',`,
      `'border border-outline-gray-2 bg-surface-base hover:bg-[var(--ct-bg-soft)] data-[state=open]:border-[var(--ct-border-strong)]',`,
    ],
  ],
  // Figma "Campo" label: 14 Medium, secondary text.
  'components/FormLabel/FormLabel.vue': [
    [
      `class="block text-sm leading-tighter text-ink-gray-6"`,
      `class="block text-sm font-medium leading-tighter text-ink-gray-6"`,
    ],
  ],

  // Figma "Pílula de status" (959:69) and "Contador" (959:76): pill shape,
  // 12px Medium, 10px side padding. Colored tones come from the tokens.
  'components/Badge/Badge.vue': [
    [
      `class="inline-flex select-none items-center gap-1 overflow-clip rounded-full leading-tighter whitespace-nowrap"`,
      `class="inline-flex select-none items-center gap-1.5 overflow-clip rounded-full font-medium leading-tighter whitespace-nowrap"`,
    ],
    [
      `subtle: 'text-ink-gray-6 bg-surface-gray-2',`,
      `subtle: 'text-[color:var(--ct-text-primary)] bg-[var(--ct-bg-panel)]',`,
    ],
    [`md: 'h-5 px-1.5 text-xs',`, `md: 'h-5 px-2.5 text-xs',`],
    [
      `lg: 'h-6 px-2 text-[13px] tracking-[0.02em]',`,
      `lg: 'h-6 px-3 text-[13px] tracking-[0.02em]',`,
    ],
  ],

  // Figma "Avatar" (959:95): without a photo, initials sit on one of seven
  // colored tones picked from the name, so the same person keeps the same color.
  'components/Avatar/Avatar.vue': [
    [
      `class="flex h-full w-full items-center justify-center uppercase select-none"`,
      `class="flex h-full w-full items-center justify-center font-medium uppercase select-none"`,
    ],
    [
      `  return classes[props.theme]
})`,
      `  if (props.theme === 'gray') {
    const tones = ${AVATAR_TONES}
    const name = String(props.label || '').trim()
    if (!name) {
      return 'bg-[var(--ct-avatar-neutral-bg)] text-[color:var(--ct-avatar-neutral-fg)]'
    }
    let hash = 0
    for (const char of name) hash = (hash * 31 + char.codePointAt(0)) >>> 0
    return tones[hash % tones.length]
  }
  return classes[props.theme]
})`,
    ],
  ],

  // Figma "Interruptor" (959:104): on = blue, off = #dcdde2.
  'components/Switch/Switch.vue': [
    [
      `? 'bg-surface-gray-10 enabled:hover:bg-surface-gray-9 active:bg-surface-gray-8 group-hover:enabled:bg-surface-gray-9'
      : 'bg-surface-gray-4 enabled:hover:bg-surface-gray-5 active:bg-surface-gray-6 group-hover:enabled:bg-surface-gray-5',`,
      `? 'bg-[var(--ct-accent)] enabled:hover:bg-[var(--ct-accent-hover)] active:bg-[var(--ct-accent-active)] group-hover:enabled:bg-[var(--ct-accent-hover)]'
      : 'bg-surface-gray-5 enabled:hover:bg-surface-gray-6 active:bg-surface-gray-6 group-hover:enabled:bg-surface-gray-6',`,
    ],
  ],

  // Figma "Caixa de seleção" (940:108): checked = blue.
  'components/Checkbox/Checkbox.vue': [
    [
      `'text-[color:var(--surface-gray-10)]',`,
      `'text-[color:var(--ct-accent)]',`,
    ],
    [
      `'group-hover:border-outline-gray-5 checked:group-hover:text-[color:var(--surface-gray-9)]'`,
      `'group-hover:border-outline-gray-5 checked:group-hover:text-[color:var(--ct-accent-hover)]'`,
    ],
    [
      `checked:hover:text-[color:var(--surface-gray-9)] checked:active:text-[color:var(--surface-gray-8)]'`,
      `checked:hover:text-[color:var(--ct-accent-hover)] checked:active:text-[color:var(--ct-accent-active)]'`,
    ],
  ],

  // Figma "Dica" (1017:1061): #1e1f23, radius 6, 12 Medium.
  'components/Tooltip/TooltipBubble.vue': [
    [
      `class="rounded-4 bg-surface-gray-10 px-2 py-1 text-xs text-ink-base shadow-xl"`,
      `class="rounded-[var(--ct-radius-sm)] bg-[var(--ct-tooltip-bg)] px-2 py-1 text-xs font-medium text-[color:var(--ct-tooltip-fg)] shadow-[var(--ct-shadow-tooltip)]"`,
    ],
    [`class="fill-surface-gray-10"`, `class="fill-[var(--ct-tooltip-bg)]"`],
  ],

  // Figma "Modal" (960:356): radius 12, soft shadow, 20 Semi Bold title.
  'components/Dialog/Dialog.vue': [
    [
      `class="fixed inset-0 z-50 bg-black-overlay-200 dark:bg-black-overlay-700 dialog-overlay outline-none"`,
      `class="fixed inset-0 z-50 bg-[var(--ct-overlay)] dialog-overlay outline-none"`,
    ],
    [
      `rounded-7 bg-surface-elevation-1 text-start align-middle shadow-xl dialog-content`,
      `rounded-[var(--ct-radius-lg)] bg-surface-elevation-1 text-start align-middle shadow-[var(--ct-shadow-modal)] dialog-content`,
    ],
    [
      `class="text-2xl-semibold leading-6 text-ink-gray-8"`,
      `class="text-[20px] font-semibold leading-7 text-ink-gray-9"`,
    ],
    [
      `<p class="text-p-base text-ink-gray-7">`,
      `<p class="text-p-base text-ink-gray-6">`,
    ],
  ],

  // Figma "Aviso" (960:402): light background in the message's color
  // (info blue, success green, warning amber, error red) instead of a dark toast.
  'components/Toast/ToastProvider.vue': [
    [
      `'group py-2.5 flex items-center px-4 bg-surface-gray-9 rounded-5 shadow-xl w-[360px] after:bg-transparent',`,
      `'group py-2.5 flex items-center gap-2.5 pl-3.5 pr-2.5 bg-[var(--ct-info-soft)] text-[color:var(--ct-info)] rounded-[var(--ct-radius-md)] shadow-lg w-[400px] after:bg-transparent',`,
    ],
    [
      `title: 'text-p-base font-medium text-ink-base',
        description: 'text-p-base text-ink-base',
        icon: 'mr-2 text-ink-base [&_svg]:size-4',`,
      `title: 'text-p-base font-medium text-current',
        description: 'text-p-base text-current',
        icon: 'text-current [&_svg]:size-5',`,
    ],
    [
      `rounded-1 text-ink-base hover:bg-surface-gray-8 size-5`,
      `rounded-1 text-current hover:bg-black/5 size-5`,
    ],
    [
      `'flex shrink-0 text-ink-blue-link font-medium py-1.5 px-2 h-7 text-base mr-2 ml-auto bg-transparent hover:bg-surface-gray-8 rounded-4 !transition-colors',`,
      `'flex shrink-0 items-center text-current font-medium px-3 h-6 text-xs mr-1 ml-auto bg-surface-base hover:bg-surface-gray-2 rounded-[var(--ct-radius-sm)] !transition-colors',`,
    ],
    [
      `'flex text-ink-blue-link font-medium py-1.5 px-2 text-base hover:bg-surface-gray-8 transition-colors',`,
      `'flex items-center text-current font-medium px-3 h-6 text-xs bg-surface-base hover:bg-surface-gray-2 rounded-[var(--ct-radius-sm)] transition-colors',`,
    ],
    [
      `error: '[&_[data-icon]]:text-ink-red-4',
        warning: '[&_[data-icon]]:text-ink-amber-4',`,
      `error: '!bg-[var(--ct-error-soft)] !text-[color:var(--ct-error)]',
        warning: '!bg-[var(--ct-warning-soft)] !text-[color:var(--ct-warning)]',
        success: '!bg-[var(--ct-success-soft)] !text-[color:var(--ct-success)]',`,
    ],
  ],

  // Figma "Aba" (959:148): the active underline tab is blue (text + line).
  'components/shared/tabs/Pill.vue': [
    [
      `props.active ? 'text-ink-gray-8' : 'text-ink-gray-5',`,
      `props.active
    ? props.variant === 'underline'
      ? 'text-[color:var(--ct-text-accent)]'
      : 'text-ink-gray-8'
    : 'text-ink-gray-5',`,
    ],
  ],
  'components/Tabs/TabList.vue': [
    [
      `<div class="size-full bg-[var(--outline-gray-8)]" />`,
      `<div class="size-full bg-[var(--ct-accent)]" />`,
    ],
  ],
  'components/TabButtons/TabButtons.vue': [
    [`? ['bg-[var(--outline-gray-8)]']`, `? ['bg-[var(--ct-accent)]']`],
  ],

  // Figma "Item da barra lateral" (960:110): 32px, radius 8, active = #e6e7eb
  // with black Medium text, hover = #f5f5f7.
  'components/Sidebar/SidebarItem.vue': [
    [
      `class="group/sidebar-item flex h-7 items-center rounded-4 transition"`,
      `class="group/sidebar-item flex h-8 items-center rounded-[var(--ct-radius-md)] transition"`,
    ],
    [
      `? 'bg-surface-elevation-3 text-ink-gray-8 shadow-sm'`,
      `? 'bg-[var(--ct-bg-panel)] font-medium text-ink-gray-9'`,
    ],
  ],
}

function inputPatches() {
  return [
    [
      `'border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-elevation-2 hover:bg-surface-gray-3 focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0',`,
      `'border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-elevation-2 hover:bg-surface-gray-3 focus:bg-surface-base focus:border-[var(--ct-accent)] focus:shadow-none focus:ring-0',`,
    ],
    [
      `'border border-outline-gray-2 bg-surface-base placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0',`,
      `'border border-outline-gray-2 bg-surface-base placeholder-ink-gray-4 hover:border-outline-gray-3 focus:bg-surface-base focus:border-[var(--ct-border-strong)] focus:shadow-[0_0_0_1px_var(--ct-border-strong)] focus:ring-0',`,
    ],
  ]
}

/** Applies `list` to `code`; throws when a `from` is missing or not unique. */
export function applyPatches(code, list, file) {
  let out = code
  for (const [from, to] of list) {
    const count = out.split(from).length - 1
    if (count !== 1) {
      throw new Error(
        `[credtech-theme] ${file}: expected 1 match, found ${count} for:\n${from}`,
      )
    }
    out = out.replace(from, () => to)
  }
  return out
}

export default function credtechFrappeUiTheme() {
  const entries = Object.entries(patches)
  return {
    name: 'credtech-frappe-ui-theme',
    enforce: 'pre',
    transform(code, id) {
      if (id.includes('?')) return null
      const path = id.replace(/\\/g, '/')
      const hit = entries.find(([file]) =>
        path.endsWith(`/frappe-ui/src/${file}`),
      )
      if (!hit) return null
      return { code: applyPatches(code, hit[1], hit[0]), map: null }
    },
  }
}
