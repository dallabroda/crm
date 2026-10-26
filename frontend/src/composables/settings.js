import { computed, ref } from 'vue'

export const mobileSidebarOpened = ref(false)

export const isMobileView = computed(() => window.innerWidth < 768)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')

// Set to open the Funnels page straight on the editor of a new funnel
export const newPipelineRequested = ref(false)
