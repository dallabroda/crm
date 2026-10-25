// The server builds side panel placeholders in English ("Add Industry...",
// "Select Deal Owner..."). Rebuild those defaults from the translated label;
// a custom placeholder is just translated.
const DEFAULTS = [
  [/^Add (.+)\.\.\.$/, 'Add {0}...'],
  [/^Select (.+)\.\.\.$/, 'Select {0}...'],
]

export function translatePlaceholder(placeholder, label, translate) {
  if (!placeholder) return ''
  for (const [pattern, message] of DEFAULTS) {
    const match = placeholder.match(pattern)
    if (match && (!label || match[1] === label)) {
      return translate(message, [translate(match[1])])
    }
  }
  return translate(placeholder)
}
