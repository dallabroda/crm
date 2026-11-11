<template>
  <!-- Figma "Configurações · Equipe · Hierarquia" (2335:9297): one full-width
       row per person in a bordered list, 32px deeper per level with a "└",
       name over role and reach, "Trocar chefe" on the right. Collapsing
       (click on a manager) and drag-and-drop stay. -->
  <div class="hierarchy-tree-row" :data-has-children="hasChildren">
    <div
      class="group flex items-center gap-3 border-b border-[var(--ct-border)] py-2.5 pr-4 select-none"
      :class="[
        rowClass,
        canEdit ? 'cursor-grab' : hasChildren ? 'cursor-pointer' : '',
        isHighlighted ? 'bg-surface-gray-1' : 'hover:bg-surface-gray-1',
        isLast ? 'border-b-0' : '',
      ]"
      :style="{ paddingLeft: `${16 + depth * 32}px` }"
      :draggable="canEdit"
      :aria-expanded="hasChildren ? !isCollapsed : undefined"
      @dragstart="canEdit && handlers.onDragStart($event, node)"
      @dragend="canEdit && handlers.onDragEnd(node)"
      @dragover.prevent="canEdit && handlers.onDragOver($event, node)"
      @dragleave="canEdit && handlers.onDragLeave(node)"
      @drop.prevent="canEdit && handlers.onDrop(node)"
      @click="hasChildren && emit('toggle', $event)"
    >
      <span
        v-if="depth"
        class="w-3 shrink-0 text-[14px] leading-5 text-[color:var(--ct-text-tertiary)]"
        aria-hidden="true"
        >└</span
      >
      <UserAvatar :user="node.user" size="xl" hide-status class="shrink-0" />

      <div class="flex min-w-0 flex-1 flex-col">
        <div class="flex min-w-0 items-center gap-2">
          <span
            class="truncate text-[14px] font-medium leading-5 text-[color:var(--ct-text-primary)]"
          >
            {{ node.full_name }}
          </span>
          <Badge
            v-if="!node.enabled"
            :label="__('disabled')"
            theme="gray"
            variant="subtle"
            size="sm"
          />
          <span
            v-if="hasChildren && isCollapsed"
            class="lucide-chevron-right size-4 shrink-0 text-[color:var(--ct-text-tertiary)]"
            aria-hidden="true"
          />
        </div>
        <span
          class="truncate text-[12px] leading-4 text-[color:var(--ct-text-tertiary)]"
        >
          {{ subtitle }}
        </span>
      </div>

      <div v-if="canEdit" class="flex shrink-0 items-center gap-1" @click.stop>
        <div
          class="flex gap-1 transition-opacity"
          :class="
            isHighlighted ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
          "
        >
          <Popover
            side="bottom"
            align="end"
            bare
            @update:open="popoverOpen = $event"
          >
            <template #trigger>
              <Button
                variant="ghost"
                icon="lucide-plus"
                :tooltip="__('Add direct reports')"
              />
            </template>
            <template #default="{ close }">
              <div
                class="mt-1 rounded-6 bg-surface-base shadow-2xl w-72 border border-outline-gray-2"
              >
                <UserMultiSelect
                  v-model="selected"
                  :candidates="getCandidates(node)"
                  :loading="candidatesLoading"
                />
                <div class="border-t p-1.5 flex justify-end">
                  <Button
                    variant="solid"
                    :disabled="!selected.length"
                    :label="__('Add ({0})', [selected.length])"
                    @click="commit(close)"
                  />
                </div>
              </div>
            </template>
          </Popover>
          <Dropdown :options="moreOptions" align="end">
            <template #default="{ open }">
              <Button
                variant="ghost"
                icon="lucide-more-horizontal"
                :class="syncDropdown(open)"
              />
            </template>
          </Dropdown>
        </div>
        <Dropdown :options="managerOptions" align="end">
          <template #default="{ open }">
            <Button
              variant="outline"
              :label="__('Change manager')"
              :class="syncManager(open)"
            />
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import UserMultiSelect from './UserMultiSelect.vue'
import { Badge, Button, Dropdown, Popover } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  hasChildren: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false },
  isLast: { type: Boolean, default: false },
  rowClass: { type: String, default: '' },
  handlers: { type: Object, required: true },
  getCandidates: { type: Function, required: true },
  candidatesLoading: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  // level in the tree (0 = top) and people below, for the indent and reach
  depth: { type: Number, default: 0 },
  reach: { type: Number, default: 0 },
  // [{ label, onClick }]: who this person can report to
  managerOptions: { type: Array, default: () => [] },
})

const emit = defineEmits(['toggle', 'bulk-add', 'remove', 'move-to-root'])

const selected = ref([])
const popoverOpen = ref(false)
const dropdownOpen = ref(false)

const managerOpen = ref(false)
const isHighlighted = computed(
  () => popoverOpen.value || dropdownOpen.value || managerOpen.value,
)

function syncDropdown(open) {
  if (dropdownOpen.value !== open) dropdownOpen.value = open
  return ''
}

function syncManager(open) {
  if (managerOpen.value !== open) managerOpen.value = open
  return ''
}

// "Gerente de Vendas · vê os cards de 2 pessoas"
const subtitle = computed(() => {
  if (!props.reach) return props.node.role_label
  const reach =
    props.reach === 1
      ? __('sees the cards of 1 person')
      : __('sees the cards of {0} people', [props.reach])
  return `${props.node.role_label} · ${reach}`
})

watch(popoverOpen, (open) => {
  if (!open) selected.value = []
})

function commit(close) {
  if (!selected.value.length) return
  emit('bulk-add', { parent: props.node, userIds: selected.value })
  selected.value = []
  close()
}

const moreOptions = computed(() => {
  const opts = []
  if (props.node.reports_to) {
    opts.push({
      label: __('Move to top level'),
      icon: 'lucide-corner-up-left',
      onClick: () => emit('move-to-root', props.node),
    })
  }
  opts.push({
    label: __('Delete'),
    icon: 'lucide-trash-2',
    onClick: () => emit('remove', props.node),
  })
  return opts
})
</script>
