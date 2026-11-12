<template>
  <div class="flex overflow-x-auto h-full">
    <Draggable
      v-if="columns"
      :list="columns"
      item-key="column"
      :disabled="options.fixedColumns"
      :delay="isTouchScreenDevice() ? 200 : 0"
      class="flex gap-4 px-3 pb-4 sm:px-6"
      @end="updateColumn"
    >
      <template #item="{ element: column }">
        <div
          v-if="!column.column.delete"
          class="flex flex-col gap-3 min-w-72 w-72 rounded-[var(--ct-radius-lg)]"
        >
          <!-- Figma "Vendas · Kanban" (791:2): status dot + stage name, ghost "+" -->
          <div class="flex h-8 gap-2 items-center group justify-between">
            <div class="flex min-w-0 items-center text-base">
              <div v-if="options.fixedColumns" class="shrink-0">
                <IndicatorIcon :class="parseColor(column.column.color)" />
              </div>
              <Popover v-else bare>
                <!-- Figma "Tarefas · Kanban" (811:2): the dot sits where the
                     fixed columns have it; it still opens the color picker -->
                <template #trigger>
                  <button
                    type="button"
                    class="flex shrink-0 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                    :aria-label="__('Color')"
                  >
                    <IndicatorIcon :class="parseColor(column.column.color)" />
                  </button>
                </template>
                <template #default>
                  <div
                    class="flex flex-col gap-3 px-3 py-2.5 min-w-40 rounded-6 bg-surface-elevation-2 shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                  >
                    <div class="flex gap-1">
                      <Button
                        v-for="color in colors"
                        :key="color"
                        variant="ghost"
                        @click="() => (column.column.color = color)"
                      >
                        <IndicatorIcon :class="parseColor(color)" />
                      </Button>
                    </div>
                    <div class="flex flex-row-reverse">
                      <Button
                        variant="solid"
                        :label="__('Apply')"
                        @click="updateColumn"
                      />
                    </div>
                  </div>
                </template>
              </Popover>
              <div class="truncate text-ink-gray-9">
                {{ __(column.column.label || column.column.name) }}
              </div>
            </div>
            <div class="flex">
              <Dropdown v-if="!options.fixedColumns" :options="actions(column)">
                <template #default>
                  <Button
                    class="opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity"
                    icon="lucide-more-horizontal"
                    variant="ghost"
                  />
                </template>
              </Dropdown>
              <Button
                icon="lucide-plus"
                variant="ghost"
                @click="options.onNewClick(column)"
              />
            </div>
          </div>
          <div class="overflow-y-auto flex flex-col gap-2 h-full">
            <Draggable
              :list="column.data"
              group="fields"
              item-key="name"
              class="flex flex-col gap-3 flex-1"
              :delay="isTouchScreenDevice() ? 200 : 0"
              :data-column="column.column.name"
              @end="updateColumn"
            >
              <template #item="{ element: fields }">
                <div
                  class="relative flex flex-col gap-3 rounded-[var(--ct-radius-lg)] border border-outline-gray-2 bg-surface-base p-4 text-base text-ink-gray-9"
                  :data-name="fields.name"
                  @click="options.onClick && options.onClick(fields)"
                >
                  <!-- Figma "Card de Kanban" (1215:1371): radius 12, border #dcdde2,
                       16px padding, 12px between title, details, divider and footer -->
                  <!-- covers the whole card so the actions row can hold its own buttons outside the link -->
                  <router-link
                    v-if="options.getRoute"
                    :to="options.getRoute(fields)"
                    class="absolute inset-0 rounded-[var(--ct-radius-lg)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-4"
                    :aria-label="fields[titleField] || __('No Title')"
                  />
                  <!-- clicks fall through to the card link; only tooltip triggers take hover -->
                  <div
                    class="relative pointer-events-none font-medium [&_.text-base]:font-medium [&_[data-slot=trigger]]:pointer-events-auto"
                  >
                    <slot
                      name="title"
                      v-bind="{ fields, titleField, itemName: fields.name }"
                    >
                      <div class="h-5 flex items-center">
                        <div v-if="fields[titleField]">
                          {{ fields[titleField] }}
                        </div>
                        <div v-else class="text-ink-gray-4">
                          {{ __('No Title') }}
                        </div>
                      </div>
                    </slot>
                  </div>
                  <!-- inlineFields: Figma "Tarefas · Kanban" (811:2) puts the
                       priority and the time on one line -->
                  <div
                    v-if="cardFields(column).length"
                    class="relative pointer-events-none [&_[data-slot=trigger]]:pointer-events-auto flex"
                    :class="
                      options.inlineFields
                        ? 'flex-row flex-wrap items-center gap-x-2 gap-y-3'
                        : 'flex-col gap-3'
                    "
                  >
                    <template v-for="value in cardFields(column)" :key="value">
                      <slot
                        name="fields"
                        v-bind="{
                          fields,
                          fieldName: value,
                          itemName: fields.name,
                        }"
                      >
                        <div v-if="fields[value]" class="truncate">
                          {{ fields[value] }}
                        </div>
                      </slot>
                    </template>
                  </div>
                  <!-- Figma "Card de Kanban": activity counters (e-mails, notes, tasks, comments) above the divider -->
                  <div
                    v-if="$slots.activity"
                    class="relative z-10 pointer-events-none [&_button]:pointer-events-auto"
                  >
                    <slot name="activity" v-bind="{ itemName: fields.name }" />
                  </div>
                  <div class="border-b border-outline-gray-2 h-px" />
                  <div
                    class="relative z-10 pointer-events-none [&_button]:pointer-events-auto"
                  >
                    <slot name="actions" v-bind="{ itemName: fields.name }">
                      <div class="flex gap-2 items-center justify-between">
                        <div></div>
                        <Button
                          icon="lucide-plus"
                          variant="ghost"
                          @click.stop.prevent
                        />
                      </div>
                    </slot>
                  </div>
                </div>
              </template>
            </Draggable>
            <div
              v-if="column.column.count < column.column.all_count"
              class="flex items-center justify-center"
            >
              <Button
                :label="__('Load More')"
                @click="emit('loadMore', column.column.name)"
              />
            </div>
          </div>
        </div>
      </template>
    </Draggable>
    <div v-if="!options.fixedColumns" class="shrink-0 min-w-64">
      <Combobox
        :model-value="null"
        :options="deletedColumns"
        @update:selected-option="(e) => addColumn(e)"
      >
        <template #trigger="{ open, setOpen }">
          <Button
            class="w-full mt-2.5 mb-1 mr-5"
            :label="__('Add Column')"
            iconLeft="lucide-plus"
            @click="setOpen(!open)"
          />
        </template>
        <template #footer>
          <Button
            class="w-full"
            :label="__('Reload Columns')"
            :iconLeft="RefreshIcon"
            @click="updateColumn(null, true)"
          />
        </template>
      </Combobox>
    </div>
  </div>
</template>
<script setup>
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { isTouchScreenDevice, colors, parseColor } from '@/utils'
import Draggable from 'vuedraggable'
import { Combobox, Dropdown, Popover } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({
      getRoute: null,
      onClick: null,
      onNewClick: null,
      // funnel stages: no reordering, recolouring, hiding or adding columns here
      fixedColumns: false,
      // card field the page shows in the card footer instead of the field list
      footerField: null,
      // card fields side by side (wrapping) instead of one per line
      inlineFields: false,
    }),
  },
})

const emit = defineEmits(['update', 'loadMore'])

const kanban = defineModel({ type: Object })

const titleField = computed(() => {
  return kanban.value?.data?.title_field
})

const columns = computed(() => {
  if (!kanban.value?.data?.data || kanban.value.data.view_type != 'kanban')
    return []
  let _columns = kanban.value.data.data

  let has_color = _columns.some((column) => column.column?.color)
  if (!has_color) {
    _columns.forEach((column, i) => {
      column.column['color'] = colors[i % colors.length]
    })
  }
  return _columns
})

const deletedColumns = computed(() => {
  const _columns = kanban.value?.data?.kanban_columns || []
  return _columns
    ?.filter((col) => col['delete'])
    .map((col) => {
      return { label: col.name, value: col.name }
    })
})

function cardFields(column) {
  return (column.fields || []).filter((f) => f !== props.options.footerField)
}

function actions(column) {
  return [
    {
      group: __('Options'),
      hideLabel: true,
      options: [
        {
          label: __('Delete'),
          icon: 'lucide-trash-2',
          onClick: () => {
            column.column['delete'] = true
            updateColumn()
          },
        },
      ],
    },
  ]
}

function addColumn(e) {
  let column = columns.value.find((col) => col.column.name == e.value)
  column.column['delete'] = false
  columns.value.splice(columns.value.indexOf(column), 1)
  columns.value.push(column)
  updateColumn()
}

function updateColumn(d, fetchNewColumns = false) {
  let toColumn = d?.to?.dataset.column
  let fromColumn = d?.from?.dataset.column
  let itemName = d?.item?.dataset.name

  let _columns = []
  columns.value.forEach((col) => {
    col.column['order'] = col.data.map((d) => d.name)
    if (col.column.page_length) {
      delete col.column.page_length
    }
    _columns.push(col.column)
  })

  let data = { kanban_columns: _columns, fetchNewColumns }

  if (toColumn != fromColumn) {
    data = {
      item: itemName,
      to: toColumn,
      from: fromColumn,
      fromIndex: d?.oldIndex,
      kanban_columns: _columns,
    }
  }

  emit('update', data)
}
</script>
