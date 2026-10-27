<template>
  <FrappeListFooter
    v-model="pageLength"
    :options="options"
    @loadMore="emit('loadMore')"
  >
    <template #right>
      <div class="flex items-center">
        <Button
          v-if="showLoadMore"
          :label="__('Load More')"
          @click="emit('loadMore')"
        />
        <div v-if="showLoadMore" class="mx-3 h-[80%] border-l" />
        <div class="text-base text-ink-gray-5">
          {{
            __('{0} of {1}', [
              options.rowCount || '0',
              options.totalCount || '0',
            ])
          }}
        </div>
      </div>
    </template>
  </FrappeListFooter>
</template>
<script setup>
// frappe-ui's list footer has "of" and "Load More" fixed in English; the counter is rebuilt here in the user's language
import { Button } from 'frappe-ui'
import { ListFooter as FrappeListFooter } from 'frappe-ui/experimental'
import { computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: () => ({ rowCount: 0, totalCount: 0 }),
  },
})

const pageLength = defineModel({ type: Number, default: 20 })
const emit = defineEmits(['loadMore'])

const showLoadMore = computed(
  () =>
    props.options.rowCount &&
    props.options.totalCount &&
    props.options.rowCount < props.options.totalCount,
)
</script>
