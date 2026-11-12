import { expect, it, vi } from 'vitest'
import { computed, nextTick, reactive, ref } from 'vue'

const route = reactive({ hash: '' })
vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push: (r) => (route.hash = r.hash) }),
}))
const { useActiveTabManager } = await import(
  '@/composables/useActiveTabManager'
)

const tab = (value) => ({ value })

it('opens a collection card on its first tab (Títulos) once the funnel is known', async () => {
  localStorage.setItem('lastDealTab', 'activity')
  route.hash = ''
  const collection = ref(false)
  const tabs = computed(() =>
    collection.value
      ? [tab('titles'), tab('activity'), tab('attachments')]
      : [tab('activity'), tab('attachments')],
  )
  const { activeTab } = useActiveTabManager(tabs, 'lastDealTab', {
    firstTabByDefault: () => collection.value,
  })
  expect(activeTab.value).toBe('activity')

  collection.value = true
  await nextTick()
  expect(activeTab.value).toBe('titles')
})

it('keeps the last visited tab on other cards', () => {
  localStorage.setItem('lastDealTab', 'attachments')
  route.hash = ''
  const tabs = computed(() => [tab('activity'), tab('attachments')])
  const { activeTab } = useActiveTabManager(tabs, 'lastDealTab', {
    firstTabByDefault: () => false,
  })
  expect(activeTab.value).toBe('attachments')
})
