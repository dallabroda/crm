import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick } from 'vue'

vi.mock('frappe-ui', () => ({
  Button: {
    props: ['label'],
    emits: ['click'],
    setup:
      (props, { emit }) =>
      () =>
        h('button', { onClick: () => emit('click') }, props.label),
  },
}))
vi.mock('frappe-ui/experimental', () => ({
  ListFooter: {
    setup:
      (_, { slots }) =>
      () =>
        h('div', slots.right?.()),
  },
}))
import ListFooter from '@/components/ListViews/ListFooter.vue'

const PT_BR = { '{0} of {1}': '{0} de {1}', 'Load More': 'Carregar mais' }

function mountFooter(options) {
  const loadMore = vi.fn()
  const root = document.createElement('div')
  const app = createApp({
    setup: () => () => h(ListFooter, { options, onLoadMore: loadMore }),
  })
  app.config.globalProperties.__ = (text, args = []) =>
    args.reduce(
      (out, arg, i) => out.replace(`{${i}}`, arg),
      PT_BR[text] || text,
    )
  app.mount(root)
  return { root, app, loadMore }
}

it('shows the row count in the user language', () => {
  const { root, app } = mountFooter({ rowCount: 10, totalCount: 10 })
  expect(root.textContent).toBe('10 de 10')
  expect(root.querySelector('button')).toBeNull()
  app.unmount()
})

it('offers to load more while rows are missing', async () => {
  const { root, app, loadMore } = mountFooter({ rowCount: 20, totalCount: 45 })
  expect(root.textContent).toContain('20 de 45')
  root.querySelector('button').click()
  await nextTick()
  expect(root.querySelector('button').textContent).toBe('Carregar mais')
  expect(loadMore).toHaveBeenCalledOnce()
  app.unmount()
})
