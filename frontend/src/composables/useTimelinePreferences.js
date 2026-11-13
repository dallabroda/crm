import { computed } from 'vue'
import { getSettings } from '@/stores/settings'
import { formatDate, timeAgo, shortTimeAgo } from '@/utils'

export function useTimelinePreferences() {
  const { _settings } = getSettings()

  const timestampFormat = computed(
    () => _settings.doc?.crm_timeline_timestamp_format || 'Relative',
  )
  // Figma "Card · Atividade": newest first unless the company chose otherwise
  const sortOrder = computed(
    () => _settings.doc?.crm_timeline_sort_order || 'Newest First',
  )

  const showExactTimestamp = computed(() => timestampFormat.value === 'Exact')
  const isNewestFirst = computed(() => sortOrder.value === 'Newest First')

  return {
    timestampFormat,
    sortOrder,
    showExactTimestamp,
    isNewestFirst,
  }
}

// Builds a { label, timeAgo } cell for list/table views, honoring the global
// FCRM Settings timestamp format. `timeAgo` is the displayed value and `label`
// is the tooltip; when "Exact" is set the two are swapped so the date shows.
// Kept here (not in utils/index.js) so the settings store is not pulled into
// the eager import graph and fetched before frappe-ui is configured.
export function timestampCell(date, short = false) {
  if (!date) return { label: '', timeAgo: '' }
  const exact = formatDate(date)
  const relative = short ? shortTimeAgo(date) : __(timeAgo(date))
  const showExact =
    getSettings()._settings.doc?.crm_timeline_timestamp_format === 'Exact'
  return {
    label: showExact ? relative : exact,
    timeAgo: showExact ? exact : relative,
  }
}
