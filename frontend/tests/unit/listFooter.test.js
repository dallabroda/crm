import { expect, it, vi } from 'vitest'
import { createApp, h, nextTick, reactive } from 'vue'
import ListFooter from '@/components/ListViews/ListFooter.vue'

const PT_BR = {
  'Showing {0}–{1} of {2} {3}': 'Mostrando {0}–{1} de {2} {3}',
  'of {0} page': 'de {0} página',
  'of {0} pages': 'de {0} páginas',
  'Next page': 'Próxima página',
  'First page': 'Primeira página',
}

const translate = (text, args = []) =>
  args.reduce((out, arg, i) => out.replace(`{${i}}`, arg), PT_BR[text] || text)
globalThis.__ = translate

function mountFooter(data) {
  const list = reactive({
    data,
    params: { filters: { status: 'Open' }, page_length: 20 },
    loading: false,
    reload: vi.fn(),
  })
  const root = document.createElement('div')
  const app = createApp({
    setup: () => () => h(ListFooter, { list, itemLabel: 'cards' }),
  })
  // the script uses the global __ (translation plugin), the template the app's
  app.config.globalProperties.__ = translate
  app.mount(root)
  const button = (label) => root.querySelector(`button[aria-label="${label}"]`)
  return { root, app, list, button }
}

it('shows the range, the total and a single page', () => {
  const { root, app, button } = mountFooter({
    row_count: 16,
    total_count: 16,
    page_length_count: 20,
  })
  expect(root.textContent).toContain('Mostrando 1–16 de 16 cards')
  expect(root.textContent).toContain('de 1 página')
  expect(button('Próxima página').disabled).toBe(true)
  expect(button('Primeira página').disabled).toBe(true)
  app.unmount()
})

it('asks the server for the next page, keeping the filters', async () => {
  const { root, app, list, button } = mountFooter({
    row_count: 20,
    total_count: 45,
    page_length_count: 20,
  })
  expect(root.textContent).toContain('de 3 páginas')
  button('Próxima página').click()
  await nextTick()
  expect(list.params).toMatchObject({
    filters: { status: 'Open' },
    start: 20,
    page_length: 20,
  })
  expect(list.reload).toHaveBeenCalledOnce()
  app.unmount()
})

it('shows the current page from the start offset', () => {
  const { root, app, button } = mountFooter({
    row_count: 5,
    total_count: 45,
    page_length_count: 20,
    start: 40,
  })
  expect(root.textContent).toContain('Mostrando 41–45 de 45 cards')
  expect(button('Próxima página').disabled).toBe(true)
  expect(button('Primeira página').disabled).toBe(false)
  app.unmount()
})
