<template>
  <div>
    <div class="mb-1 flex items-center justify-stretch gap-2 py-1 text-base">
      <div class="inline-flex items-center flex-wrap gap-1 text-ink-gray-5">
        <Avatar
          :image="call._caller.image"
          :label="call._caller.label"
          size="md"
        />
        <span class="font-medium text-ink-gray-8 ml-1">
          {{ call._caller.label }}
        </span>
        <span>{{
          call.type == 'Incoming'
            ? __('has reached out')
            : __('has made a call')
        }}</span>
      </div>
      <div class="ml-auto whitespace-nowrap">
        <TimelineTimestamp :date="call.creation" />
      </div>
    </div>
    <!-- Figma "Card · Atividade" call card: title and avatars, then the date
         (12px), the status badge and an outline "Ouvir ligação" button -->
    <div
      class="flex cursor-pointer flex-col gap-2.5 rounded-[var(--ct-radius-md)] border border-[var(--ct-border-soft)] bg-surface-base px-3 py-[11px] text-ink-gray-9 transition-colors hover:bg-[var(--ct-bg-soft)]"
      @click="showCallLogDetailModal = true"
    >
      <div class="flex items-center justify-between">
        <div class="text-base font-medium leading-5">
          {{
            call.type == 'Incoming' ? __('Inbound Call') : __('Outbound Call')
          }}
        </div>
        <MultipleAvatar
          :avatars="[
            {
              image: call._caller.image,
              label: call._caller.label,
              name: call._caller.label,
            },
            {
              image: call._receiver.image,
              label: call._receiver.label,
              name: call._receiver.label,
            },
          ]"
          size="sm"
        />
      </div>
      <div class="flex min-h-8 flex-wrap items-center gap-2">
        <span
          class="inline-flex items-center gap-1.5 text-xs leading-4 text-ink-gray-6"
        >
          <span class="lucide-calendar size-3.5 shrink-0" aria-hidden="true" />
          {{ formatDate(call.creation, 'MMM D, dddd') }}
        </span>
        <Badge
          :label="getCallStatusLabel(call.status, call.type)"
          :theme="statusColorMap[call.status]"
        />
        <Button
          v-if="call.recording_url"
          class="ml-auto"
          variant="outline"
          iconLeft="lucide-play"
          :label="
            call.show_recording ? __('Hide Recording') : __('Ouvir ligação')
          "
          @click.stop="call.show_recording = !call.show_recording"
        />
      </div>
      <div
        v-if="
          call.show_recording &&
          call.recording_url &&
          callLog?.data?.recording_url_path
        "
        class="flex flex-col items-center justify-between"
        @click.stop
      >
        <AudioPlayer :src="callLog.data.recording_url_path" />
      </div>
    </div>
    <CallLogDetailModal
      v-model="showCallLogDetailModal"
      v-model:callLog="callLog"
    />
  </div>
</template>
<script setup>
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AudioPlayer from '@/components/Activities/AudioPlayer.vue'
import CallLogDetailModal from '@/components/Modals/CallLogDetailModal.vue'
import TimelineTimestamp from '@/components/Activities/TimelineTimestamp.vue'
import { getCallStatusLabel, statusColorMap } from '@/utils/callLog.js'
import { formatDate } from '@/utils'
import { Avatar, Badge, Button, createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const props = defineProps({
  activity: { type: Object, default: () => ({}) },
})

const call = reactive(props.activity)

const callLog = createResource({
  url: 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log',
  params: { name: call.name },
  cache: ['call_log', call.name],
  auto: true,
})
const showCallLogDetailModal = ref(false)
</script>
