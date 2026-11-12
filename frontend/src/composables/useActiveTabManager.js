import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDebounceFn, useStorage } from '@vueuse/core'

// options.firstTabByDefault(): open on the first tab instead of the last one
// visited (e.g. "Títulos" on a collection card); a tab in the URL still wins
export function useActiveTabManager(tabs, storageKey, options = {}) {
  const lastVisitedTab = useStorage(storageKey, 'activity')
  const route = useRoute()
  const router = useRouter()

  const changeTabTo = (tabName) => {
    if (!hasTab(tabName)) return
    activeTab.value = tabName
  }

  const preserveLastVisitedTab = useDebounceFn((tabName) => {
    lastVisitedTab.value = tabName
  }, 300)

  function setActiveTabInUrl(tabName) {
    let hash = '#' + tabName
    if (route.hash === hash) return
    router.push({ ...route, hash })
  }

  function getActiveTabFromUrl() {
    return route.hash.replace('#', '')
  }

  function hasTab(tabName) {
    return tabs.value?.some((tab) => tab.value === tabName)
  }

  function firstTab() {
    return tabs.value?.[0]?.value
  }

  function getActiveTab() {
    let _activeTab = getActiveTabFromUrl()
    if (_activeTab) {
      if (hasTab(_activeTab)) {
        preserveLastVisitedTab(_activeTab)
        return _activeTab
      }
      return firstTab()
    }

    if (options.firstTabByDefault?.()) return firstTab()

    if (hasTab(lastVisitedTab.value)) return lastVisitedTab.value

    return firstTab()
  }

  const activeTab = ref(getActiveTab())

  watch(activeTab, (tabName) => {
    setActiveTabInUrl(tabName)
    preserveLastVisitedTab(tabName)
  })

  watch(
    () => route.hash,
    (tabValue) => {
      if (!tabValue) return

      let tabName = tabValue.replace('#', '')
      if (!hasTab(tabName)) tabName = firstTab()

      preserveLastVisitedTab(tabName)
      activeTab.value = tabName
    },
  )

  watch(tabs, (newTabs, oldTabs) => {
    // the tabs load with the document: when the first tab changes to the
    // default one (the card turned out to be a collection card), open it
    if (
      options.firstTabByDefault?.() &&
      newTabs?.[0]?.value !== oldTabs?.[0]?.value
    ) {
      activeTab.value = firstTab()
      return
    }
    activeTab.value = getActiveTab()
  })

  return { activeTab, changeTabTo }
}
