<template>
  <div class="flex flex-1 flex-col gap-6">
    <SettingsRow>
      <template #label>
        {{ __('Enable enrichment') }}
      </template>
      <template #description>
        {{
          __(
            'Fill in company details on Leads, Deals and Organizations from their website.',
          )
        }}
      </template>
      <Switch
        :model-value="Boolean(doc.enabled)"
        size="sm"
        @update:model-value="(value) => emit('toggle', 'enabled', value)"
      />
    </SettingsRow>

    <template v-if="doc.enabled">
      <SettingsRow>
        <template #label>
          {{ __('Maximum pages') }}
        </template>
        <template #description>
          {{
            __(
              'Maximum number of pages that can be crawled during a single enrichment run.',
            )
          }}
        </template>
        <div class="flex flex-col items-end">
          <!-- Not :error: it renders inside the w-24 box and gets squeezed. -->
          <FormControl
            :model-value="maxPages ?? doc.max_pages"
            type="number"
            min="1"
            :max="maxPagesLimit"
            class="ct-field-48 w-24"
            variant="outline"
            size="lg"
            @update:model-value="
              (value: string | number) => emit('update:maxPages', value)
            "
          />
          <ErrorMessage
            v-if="maxPagesError"
            class="mt-1 max-w-60 text-right"
            :message="maxPagesError"
          />
        </div>
      </SettingsRow>

      <SettingsRow>
        <template #label>
          {{ __('Auto-enrich new records') }}
        </template>
        <template #description>
          {{
            __(
              'Automatically enrich new Leads, Deals and Organizations in the background when they have a website. When off, use the Enrich button on the record.',
            )
          }}
        </template>
        <Switch
          :model-value="Boolean(doc.auto_enrich)"
          size="sm"
          @update:model-value="(value) => emit('toggle', 'auto_enrich', value)"
        />
      </SettingsRow>
    </template>
  </div>
</template>

<script setup lang="ts">
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { ErrorMessage, FormControl, Switch } from 'frappe-ui'
import type { EnrichmentSettingsDoc } from './types'

// Nothing saves here: the parent holds every change (even hidden ones) until
// the header Update.
withDefaults(
  defineProps<{
    doc: EnrichmentSettingsDoc
    // Held apart from doc until Update, so half-typed input isn't stored.
    maxPages?: string | number
    maxPagesError?: string
    maxPagesLimit: number
  }>(),
  {
    maxPages: undefined,
    maxPagesError: '',
  },
)

const emit = defineEmits<{
  toggle: [fieldname: 'enabled' | 'auto_enrich', value: boolean]
  'update:maxPages': [value: string | number]
}>()
</script>
