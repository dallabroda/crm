<template>
  <Button
    v-if="context?.enabled"
    variant="subtle"
    iconLeft="lucide-upload"
    :label="__('Import titles')"
    @click="open"
  />
  <Dialog v-model:open="show" :title="__('Import titles from a spreadsheet')" size="3xl">
    <template #default>
      <div class="flex flex-col gap-4 py-1">
        <!-- 1. Arquivo -->
        <div class="flex items-center justify-between gap-3">
          <div class="text-p-sm text-ink-gray-6">
            {{ __('Send a .xlsx or .csv file with one title per line. The first line must have the column names.') }}
            <div class="mt-1">
              {{ __('Cards are grouped by: {0}.', [groupingLabel]) }}
            </div>
          </div>
          <FileUploader file-types=".xlsx,.csv" :validate-file="validateFile" @success="onUploaded">
            <template #default="{ openFileSelector, uploading }">
              <Button
                :loading="uploading"
                :label="file ? __('Change file') : __('Choose file')"
                iconLeft="lucide-file-spreadsheet"
                @click="openFileSelector()"
              />
            </template>
          </FileUploader>
        </div>
        <div v-if="file" class="text-sm text-ink-gray-7">
          {{ file.file_name }} · {{ __('{0} lines', [columns?.rows || 0]) }}
        </div>

        <!-- 2. Colunas -->
        <div v-if="columns" class="flex flex-col gap-2">
          <div class="text-base-medium text-ink-gray-8">{{ __('Which column is each field?') }}</div>
          <div class="grid grid-cols-3 gap-3">
            <FormControl
              v-for="target in columns.targets"
              :key="target.key"
              v-model="mapping[target.key]"
              type="select"
              :label="target.label + (target.required ? ' *' : '')"
              :options="columnOptions"
              @update:modelValue="result = null"
            />
          </div>
          <div class="text-p-xs text-ink-gray-5">
            {{ __('Species only comes in when the column has a registry code (DMI, DSI, CCB...): there is no default.') }}
          </div>
        </div>

        <!-- 3. Prévia -->
        <div v-if="result" class="flex flex-col gap-2 rounded border border-outline-gray-2 p-3">
          <div class="text-base-medium text-ink-gray-8">{{ __('Preview (nothing saved yet)') }}</div>
          <div class="grid grid-cols-3 gap-2 text-sm text-ink-gray-7">
            <div>{{ __('Valid lines: {0} of {1}', [result.valid, result.rows]) }}</div>
            <div>{{ __('New cards: {0}', [result.cards_new]) }}</div>
            <div>{{ __('Cards updated: {0}', [result.cards_update]) }}</div>
            <div>{{ __('New titles: {0}', [result.titles_new]) }}</div>
            <div>{{ __('Titles updated: {0}', [result.titles_update]) }}</div>
            <div>{{ __('Already at CENPROT (kept): {0}', [result.titles_locked]) }}</div>
            <div>{{ __('New people (contacts): {0}', [result.people_new]) }}</div>
            <div>{{ __('New companies: {0}', [result.companies_new]) }}</div>
            <div>{{ __('Lines with notes: {0}', [result.warnings]) }}</div>
          </div>
          <div v-if="result.problem_count" class="mt-1">
            <div class="text-sm-medium text-ink-red-4">
              {{ __('{0} lines will be left out:', [result.problem_count]) }}
            </div>
            <div class="max-h-36 overflow-y-auto text-p-xs text-ink-gray-6">
              <div v-for="problem in result.problems" :key="problem.line">
                {{ __('Line {0}: {1}', [problem.line, problem.message]) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          v-if="columns"
          :label="__('Preview')"
          :loading="busy === 'preview'"
          @click="runPreview"
        />
        <Button
          v-if="result && result.valid"
          variant="solid"
          :label="__('Import {0} titles', [result.valid])"
          :loading="busy === 'start'"
          @click="startImport"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Button, Dialog, FileUploader, FormControl, call, toast } from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

// Importação de títulos por planilha no funil de Cobrança (credtech#315). O app cred_hub responde; fora do funil
// de Cobrança (ou sem permissão de criar card) o botão não aparece.
const API = 'cred_hub.collection.importer.'

const props = defineProps({
  pipeline: { type: String, default: '' },
})
const emit = defineEmits(['done'])

const context = ref(null)
const show = ref(false)
const file = ref(null)
const columns = ref(null)
const mapping = ref({})
const result = ref(null)
const busy = ref('')

const groupingLabel = computed(() =>
  context.value?.grouping === 'Debtor' ? __('debtor') : __('debtor and cedente'),
)
const columnOptions = computed(() => [
  { label: __('(not in the spreadsheet)'), value: '' },
  ...(columns.value?.headers || []).map((header, index) => ({
    label: header || __('Column {0}', [index + 1]),
    value: String(index),
  })),
])

onMounted(async () => {
  try {
    context.value = await call(API + 'get_context', { pipeline: props.pipeline })
  } catch {
    context.value = null
  }
})

function open() {
  file.value = null
  columns.value = null
  result.value = null
  mapping.value = {}
  show.value = true
}

function validateFile(selected) {
  const name = (selected.name || '').toLowerCase()
  if (!name.endsWith('.xlsx') && !name.endsWith('.csv')) {
    return __('Send the spreadsheet as .xlsx or .csv.')
  }
}

async function onUploaded(uploaded) {
  file.value = uploaded
  result.value = null
  try {
    columns.value = await call(API + 'columns', { file_url: uploaded.file_url })
    const suggested = columns.value.suggested || {}
    mapping.value = Object.fromEntries(
      columns.value.targets.map((t) => [t.key, suggested[t.key] !== undefined ? String(suggested[t.key]) : '']),
    )
  } catch (err) {
    columns.value = null
    toast.error(err.messages?.[0] || err.message || __('Could not read the spreadsheet.'))
  }
}

function cleanMapping() {
  return Object.fromEntries(Object.entries(mapping.value).filter(([, v]) => v !== '' && v !== null))
}

async function runPreview() {
  busy.value = 'preview'
  try {
    result.value = await call(API + 'preview', { file_url: file.value.file_url, mapping: cleanMapping() })
  } catch (err) {
    result.value = null
    toast.error(err.messages?.[0] || err.message || __('Could not check the spreadsheet.'))
  } finally {
    busy.value = ''
  }
}

async function startImport() {
  busy.value = 'start'
  try {
    await call(API + 'start', { file_url: file.value.file_url, mapping: cleanMapping() })
    toast.success(__('Import started. You get a notification with the summary when it ends.'))
    show.value = false
    emit('done')
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Could not start the import.'))
  } finally {
    busy.value = ''
  }
}
</script>
