import { expect, it, vi } from 'vitest'
import { createApp, h } from 'vue'

vi.mock('frappe-ui', () => ({ Dropdown: { render: () => null } }))
vi.mock('@/components/Icon.vue', () => ({ default: { render: () => null } }))
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'

const PT_BR = { Sales: 'Vendas', Collections: 'Cobrança', Deals: 'Negócios' }

function titleOf(props) {
  const root = document.createElement('div')
  const app = createApp({ setup: () => () => h(ViewBreadcrumbs, props) })
  app.config.globalProperties.__ = (text) => PT_BR[text] || text
  app.component('RouterLink', {
    setup:
      (_, { slots }) =>
      () =>
        h('a', slots.default?.()),
  })
  app.mount(root)
  const text = root.querySelector('a').textContent.trim()
  app.unmount()
  return text
}

it('translates the funnel name the same way the sidebar does', () => {
  expect(titleOf({ routeName: 'Deals', title: 'Sales' })).toBe('Vendas')
  expect(titleOf({ routeName: 'Deals', title: 'Collections' })).toBe('Cobrança')
})

it('keeps a custom funnel name as typed', () => {
  expect(titleOf({ routeName: 'Deals', title: 'Obras 2026' })).toBe(
    'Obras 2026',
  )
})

it('falls back to the translated route name', () => {
  expect(titleOf({ routeName: 'Deals' })).toBe('Negócios')
})
