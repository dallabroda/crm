<template>
  <!-- Figma "Card · Tarefas" (801:2): one bordered card per task (radius
       12, 16px padding, 8px apart); assignee, due date and a priority pill -->
  <div v-if="tasks.length" class="flex flex-col gap-2">
    <div v-for="task in tasks" :key="task.name">
      <div
        class="activity flex cursor-pointer items-center gap-6 rounded-[var(--ct-radius-lg)] border border-[var(--ct-border)] p-4 transition-colors hover:bg-[var(--ct-bg-soft)]"
        @click="modalRef.showTask(task)"
      >
        <div class="flex flex-1 flex-col gap-2 text-base truncate">
          <div class="font-medium text-ink-gray-9 truncate">
            {{ task.title }}
          </div>
          <div class="flex flex-wrap items-center gap-4 text-ink-gray-6">
            <div class="flex items-center gap-2">
              <UserAvatar :user="task.assigned_to" size="sm" />
              {{ getUser(task.assigned_to).full_name }}
            </div>
            <div v-if="task.due_date">
              <Tooltip
                :text="formatDate(task.due_date, 'ddd, MMM D, YYYY | hh:mm a')"
              >
                <div class="flex items-center gap-1.5">
                  <CalendarIcon />
                  <div>{{ formatDate(task.due_date, 'D MMM, hh:mm a') }}</div>
                </div>
              </Tooltip>
            </div>
            <TaskPriorityBadge :priority="task.priority" />
          </div>
        </div>
        <div class="flex items-center gap-1">
          <Dropdown
            :options="taskStatusOptions(modalRef.updateTaskStatus, task)"
          >
            <Button
              :tooltip="__('Change Status')"
              variant="ghost"
              class="hover:bg-surface-gray-4"
              @click.stop.prevent
            >
              <TaskStatusIcon :status="task.status" />
            </Button>
          </Dropdown>
          <Dropdown
            :options="[
              {
                label: __('Delete'),
                icon: 'lucide-trash-2',
                onClick: () => {
                  $dialog({
                    title: __('Delete Task'),
                    message: __('Are you sure you want to delete this task?'),
                    actions: [
                      {
                        label: __('Delete'),
                        theme: 'red',
                        variant: 'solid',
                        onClick({ close }) {
                          modalRef.deleteTask(task.name)
                          close()
                        },
                      },
                    ],
                  })
                },
              },
            ]"
          >
            <Button
              icon="lucide-more-horizontal"
              variant="ghost"
              class="hover:bg-surface-gray-4 text-ink-gray-9"
              @click.stop.prevent
            />
          </Dropdown>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityBadge from '@/components/TaskPriorityBadge.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatDate, taskStatusOptions } from '@/utils'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { Tooltip, Dropdown } from 'frappe-ui'

defineProps({
  tasks: { type: Array, default: () => [] },
  modalRef: { type: Object, default: () => ({}) },
})

const { getUser } = usersStore()
const { $dialog } = globalStore()
</script>
