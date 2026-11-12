<!-- eslint-disable vue/no-v-html -->
<template>
  <ListView
    :columns="fillColumns(columns)"
    :rows="rows"
    :options="{
      onRowClick: (row) => emit('showTask', row.name),
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="h-[34px] !rounded-[var(--ct-radius-md)] mx-3 sm:mx-6"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        class="!text-base"
        :item="column"
        @columnWidthUpdated="(e) => onColumnWidthUpdated(e, column)"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghost"
          class="!h-4"
          @click="() => emit('applyLikeFilter')"
        >
          <HeartIcon
            class="h-4 w-4"
            :class="isLikeFilterApplied ? 'fill-red-500 text-red-500' : ''"
          />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      class="mx-3 sm:mx-6"
      :rows="rows"
      doctype="CRM Task"
    >
      <div v-if="column.key === 'due_date' && item">
        <Tooltip :text="item && formatDate(item, 'ddd, MMM D, YYYY | hh:mm a')">
          <div class="flex items-center gap-2 truncate text-base">
            <div><CalendarIcon /></div>
            <div class="truncate">
              {{ formatDate(item, 'D MMM, hh:mm a') }}
            </div>
          </div>
        </Tooltip>
      </div>
      <ListRowItem
        v-else
        :item="item"
        :align="column.align"
        class="overflow-hidden"
      >
        <template #prefix>
          <!-- Figma "Tarefas · Lista" (809:2): 24px avatar -->
          <div v-if="column.key === 'assigned_to'">
            <UserAvatar
              v-if="item.full_name"
              class="flex items-center"
              :user="item.name"
              :label="item.label"
              size="md"
            />
          </div>
        </template>
        <template #default="{ label }">
          <!-- Figma "Tarefas · Lista" (809:2): status and priority as pills -->
          <TaskStatusBadge
            v-if="column.key === 'status'"
            :status="item"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          />
          <TaskPriorityBadge
            v-else-if="column.key === 'priority'"
            :priority="item"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          />
          <div
            v-else-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="column.type === 'Text Editor'"
            class="truncate text-base h-4 [&>p]:truncate"
            v-html="sanitizeHTML(item)"
          />
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              variant="ghost"
              @click.stop.prevent="
                () => emit('likeDoc', { name: row.name, liked: isLiked(item) })
              "
            >
              <HeartIcon
                class="h-4 w-4"
                :class="isLiked(item) ? 'fill-red-500 text-red-500' : ''"
              />
            </Button>
          </div>
          <RatingInput
            v-else-if="column.type === 'Rating'"
            :value="item"
            class="!opacity-100 flex-nowrap overflow-auto"
            :disabled="true"
            :max="column.options || 5"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          />
          <div
            v-else-if="column.key === 'reference_docname' && (label || item)"
            class="truncate text-base"
          >
            <router-link
              v-if="row.reference_doctype === 'CRM Deal' || String(item || label).startsWith('CRM-DEAL')"
              :to="{ name: 'Deal', params: { dealId: item || label } }"
              class="inline-flex items-center gap-1 font-medium text-ink-gray-9 hover:underline hover:text-blue-600"
              @click.stop
            >
              <span class="rounded bg-surface-gray-3 px-1.5 py-0.5 text-xs text-ink-gray-6 font-normal">Card</span>
              {{ item || label }}
            </router-link>
            <router-link
              v-else-if="row.reference_doctype === 'CRM Lead' || String(item || label).startsWith('CRM-LEAD')"
              :to="{ name: 'Lead', params: { leadId: item || label } }"
              class="inline-flex items-center gap-1 font-medium text-ink-gray-9 hover:underline hover:text-blue-600"
              @click.stop
            >
              <span class="rounded bg-surface-gray-3 px-1.5 py-0.5 text-xs text-ink-gray-6 font-normal">Lead</span>
              {{ item || label }}
            </router-link>
            <span v-else>{{ getLabel(label, column) }}</span>
          </div>
          <div
            v-else-if="label"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ getLabel(label, column) }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="lucide-more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-if="list?.data"
    class="border-t border-surface-gray-3 px-3 sm:px-6"
    :list="list"
    :itemLabel="__('Tasks').toLowerCase()"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="CRM Task"
    :options="{
      hideAssign: true,
    }"
  />
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import TaskStatusBadge from '@/components/TaskStatusBadge.vue'
import TaskPriorityBadge from '@/components/TaskPriorityBadge.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  formatDate,
  isTranslatable,
  formatDuration,
  sanitizeHTML,
  fillColumns,
} from '@/utils'
import { Dropdown, Tooltip } from 'frappe-ui'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
} from 'frappe-ui/experimental'
import ListFooter from '@/components/ListViews/ListFooter.vue'
import { sessionStore } from '@/stores/session'
import { ref, computed, watch } from 'vue'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'showTask',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })

function onColumnWidthUpdated({ width, save }, column) {
  column.width = width
  if (save) emit('columnWidthUpdated', column)
}

function getLabel(label, column) {
  if (column.type === 'Duration') return formatDuration(label)
  if (column.options && isTranslatable(column.options)) return __(label)
  // Select values (status, priority) are stored in English
  if (column.type === 'Select') return __(label)
  return label
}

const isLikeFilterApplied = computed(() => {
  return list.value.params?.filters?._liked_by ? true : false
})

const { user } = sessionStore()

function isLiked(item) {
  if (item) {
    let likedByMe = JSON.parse(item)
    return likedByMe.includes(user)
  }
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})

const listBulkActionsRef = ref(null)

defineExpose({
  customListActions: computed(
    () => listBulkActionsRef.value?.customListActions,
  ),
})
</script>
