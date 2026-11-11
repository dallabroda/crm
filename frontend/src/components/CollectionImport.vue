<template>
  <Button
    v-if="context?.enabled"
    variant="outline"
    iconLeft="lucide-upload"
    :label="__('Import titles')"
    @click="open"
  />
  <!-- Figma "Cobrança · Lista · Importar títulos" (1331:19905) -->
  <Dialog v-model:open="show" :title="__('Import titles from a spreadsheet')" size="3xl">
    <template #default>
      <div class="ct-collection-import flex flex-col gap-4">
        <!-- 1. Arquivo -->
        <p class="text-base leading-5 text-ink-gray-6">
          {{ __('Send a .xlsx or .csv file with one title per line. The first line must have the column names.') }}
          {{ __('Cards are grouped by: {0}.', [groupingLabel]) }}
        </p>
        <div class="flex items-center gap-3">
          <!-- Figma (designer update, 1992647574): file name first, button after it -->
          <div v-if="file" class="min-w-0 truncate text-base text-ink-gray-6">
            {{ file.file_name }} · {{ __('{0} lines', [columns?.rows || 0]) }}
          </div>
          <FileUploader file-types=".xlsx,.csv" :validate-file="validateFile" @success="onUploaded">
            <template #default="{ openFileSelector, uploading }">
              <Button
                variant="outline"
                class="ct-btn-accent-text"
                :loading="uploading"
                :label="file ? __('Change file') : __('Choose file')"
                iconLeft="lucide-file-spreadsheet"
                @click="openFileSelector()"
              />
            </template>
          </FileUploader>
        </div>

        <!-- 2. Colunas -->
        <div v-if="columns" class="flex flex-col gap-4">
          <div class="text-base font-semibold leading-5 text-ink-gray-9">{{ __('Which column is each field?') }}</div>
          <div class="ct-columns grid grid-cols-3 gap-3">
            <FormControl
              v-for="target in columns.targets"
              :key="target.key"
              v-model="mapping[target.key]"
              type="select"
              variant="outline"
              :label="target.label + (target.required ? ' *' : '')"
              :options="columnOptions"
              @update:modelValue="result = null"
            />
          </div>
          <div class="text-xs leading-4 text-ink-gray-6">
            {{ __('Species only comes in when the column has a registry code (DMI, DSI, CCB...): there is no default.') }}
          </div>
        </div>

        <!-- 3. Prévia -->
        <div
          v-if="result"
          class="flex flex-col gap-3 rounded-[var(--ct-radius-md)] bg-[var(--ct-bg-soft)] p-4"
        >
          <div class="text-base font-semibold leading-5 text-ink-gray-9">{{ __('Preview (nothing saved yet)') }}</div>
          <!-- Figma "Números": 222px items, 42px between columns, 8px between rows -->
          <div class="grid max-w-[486px] grid-cols-2 gap-x-[42px] gap-y-2">
            <div
              v-for="stat in previewStats"
              :key="stat.label"
              class="flex items-baseline justify-between gap-2"
            >
              <span class="text-xs leading-4 text-ink-gray-6">{{ stat.label }}</span>
              <span class="text-base font-semibold leading-5 tabular-nums text-ink-gray-9">{{ stat.value }}</span>
            </div>
          </div>
          <template v-if="result.problem_count">
            <!-- Figma "Linhas de fora" (designer update): black title, white
                 box with the lines in secondary gray -->
            <div class="text-base font-semibold leading-5 text-ink-gray-9">
              {{ __('{0} lines will be left out:', [result.problem_count]) }}
            </div>
            <div
              class="flex max-h-36 flex-col gap-1 overflow-y-auto rounded-[var(--ct-radius-sm)] bg-surface-base px-3 py-2 text-xs leading-4 text-ink-gray-6"
            >
              <div v-for="problem in result.problems" :key="problem.line">
                {{ __('Line {0}: {1}', [problem.line, problem.message]) }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>
    <template #actions>
      <!-- Figma "Rodapé" (the gray band is the Dialog's) -->
      <div class="flex justify-end gap-3">
        <!-- Figma "Botão" Destrutivo (designer update, 1992648471) -->
        <Button
          variant="solid"
          theme="red"
          :label="__('Cancel')"
          @click="show = false"
        />
        <Button
          v-if="columns"
          variant="outline"
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
// label/value pairs of the preview (Figma "Números")
const previewStats = computed(() => {
  const r = result.value || {}
  return [
    { label: __('Valid lines'), value: __('{0} of {1}', [r.valid, r.rows]) },
    { label: __('New cards'), value: r.cards_new },
    { label: __('Cards updated'), value: r.cards_update },
    { label: __('New titles'), value: r.titles_new },
    { label: __('Titles updated'), value: r.titles_update },
    { label: __('Already at CENPROT (kept)'), value: r.titles_locked },
    { label: __('New people (contacts)'), value: r.people_new },
    { label: __('New companies'), value: r.companies_new },
    { label: __('Lines with notes'), value: r.warnings },
  ]
})
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
