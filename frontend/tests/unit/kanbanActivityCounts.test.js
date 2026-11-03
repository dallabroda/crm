import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

const push = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }))
vi.mock('frappe-ui', () => ({
  Tooltip: {
    setup:
      (_, { slots }) =>
      () =>
        slots.default?.(),
  },
}))
import KanbanActivityCounts from '@/components/Kanban/KanbanActivityCounts.vue'

function mountCounts(counts) {
  const root = document.createElement('div')
  const app = createApp({
    setup: () => () =>
      h(KanbanActivityCounts, { route: { name: 'Deal' }, counts }),
  })
  app.mount(root)
  return { root, app }
}

it('shows every icon, with the number only when there is activity', () => {
  const { root, app } = mountCounts({
    emails: 3,
    notes: 0,
    tasks: undefined,
    comments: 2,
  })
  const buttons = [...root.querySelectorAll('button')]
  expect(buttons).toHaveLength(4)
  expect(buttons.map((b) => b.textContent.trim())).toEqual(['3', '', '', '2'])
  // blue with the number when there is activity, gray icon alone at zero
  // (Figma "Card de Kanban", designer comment on 791:2)
  expect(buttons[0].className).toContain('--ct-text-accent')
  expect(buttons[1].className).toContain('text-ink-gray-4')
  app.unmount()
})

it('opens the matching tab of the card', async () => {
  const { root, app } = mountCounts({ notes: 1 })
  root.querySelectorAll('button')[1].click()
  await nextTick()
  expect(push).toHaveBeenCalledWith({ name: 'Deal', hash: '#notes' })
  app.unmount()
})
