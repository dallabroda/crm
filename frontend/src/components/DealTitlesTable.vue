<template>
  <div class="flex flex-col gap-4 p-5 bg-surface-white rounded-lg border border-outline-gray-2">
    <!-- Header com resumo e botão de adicionar -->
    <div class="flex items-center justify-between pb-3 border-b border-outline-gray-2">
      <div class="flex items-center gap-3">
        <span class="text-lg-semibold text-ink-gray-9">
          {{ __('Títulos e Duplicatas Vencidas') }}
        </span>
        <Badge
          :label="`${titles.length} título(s)`"
          variant="subtle"
          theme="gray"
        />
        <Badge
          v-if="totalAmount > 0"
          :label="`Total: ${formatMoney(totalAmount)} em aberto`"
          variant="subtle"
          theme="blue"
        />
      </div>
      <Button
        variant="subtle"
        iconLeft="lucide-plus"
        :label="__('Adicionar Título')"
        @click="showAddModal = true"
      />
    </div>

    <!-- Hidden file input for uploading attachments -->
    <input
      ref="fileInputRef"
      type="file"
      accept="application/pdf,image/*"
      class="hidden"
      @change="onFileSelected"
    />

    <!-- Tabela de Títulos -->
    <div v-if="titles.length" class="overflow-x-auto">
      <table class="w-full text-left border-collapse text-p-sm">
        <thead>
          <tr class="border-b border-outline-gray-2 text-ink-gray-5 font-medium">
            <th class="py-2.5 px-3">{{ __('Nº Título') }}</th>
            <th class="py-2.5 px-3">{{ __('Nosso Nº') }}</th>
            <th class="py-2.5 px-3">{{ __('Vencimento') }}</th>
            <th class="py-2.5 px-3 text-right">{{ __('Valor Original') }}</th>
            <th class="py-2.5 px-3 text-right">{{ __('Atualizado') }}</th>
            <th class="py-2.5 px-3 min-w-[200px]">{{ __('Título cartório') }}</th>
            <th class="py-2.5 px-3 min-w-[140px]">{{ __('Anexos') }}</th>
            <th class="py-2.5 px-3">{{ __('Status cartório') }}</th>
            <th class="py-2.5 px-3 text-center min-w-[140px]">{{ __('Ações') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-gray-1">
          <tr
            v-for="title in titles"
            :key="title.name || title.title_number"
            class="hover:bg-surface-gray-1 transition-colors"
          >
            <!-- Nº Título -->
            <td class="py-3 px-3 font-medium text-ink-gray-9">
              <span>{{ title.title_number }}</span>
            </td>

            <!-- Nosso Nº -->
            <td class="py-3 px-3 text-ink-gray-7">
              {{ title.our_number || '—' }}
            </td>

            <!-- Vencimento no formato brasileiro dd mmm aaaa + Dias de Atraso -->
            <td class="py-3 px-3">
              <div class="flex flex-col">
                <span class="text-ink-gray-9 font-medium">{{ formatBrazilianDate(title.due_date) }}</span>
                <span
                  v-if="daysOverdue(title.due_date) > 0"
                  class="text-xs text-red-600 font-medium"
                >
                  {{ daysOverdue(title.due_date) }} dias de atraso
                </span>
              </div>
            </td>

            <!-- Valor Original -->
            <td class="py-3 px-3 text-right text-ink-gray-7">
              {{ formatMoney(title.original_amount) }}
            </td>

            <!-- Valor Atualizado -->
            <td class="py-3 px-3 text-right font-semibold text-ink-gray-9">
              {{ formatMoney(title.updated_amount || title.original_amount) }}
            </td>

            <!-- Título cartório (Dropdown obrigatório) -->
            <td class="py-3 px-3">
              <select
                :value="title.species || ''"
                class="w-full text-xs rounded border border-outline-gray-2 bg-surface-white px-2 py-1.5 text-ink-gray-9 focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600"
                @change="onSpeciesChange(title, $event.target.value)"
              >
                <option value="">{{ __('Selecionar') }}</option>
                <option
                  v-for="opt in speciesOptions"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.label }}
                </option>
              </select>
            </td>

            <!-- Anexos com alerta visual -->
            <td class="py-3 px-3">
              <!-- Se tem arquivo anexado -->
              <div v-if="title.attachment" class="flex items-center gap-1 text-ink-gray-8">
                <Icon icon="lucide-paperclip" class="size-3.5 text-blue-600 shrink-0" />
                <a
                  :href="title.attachment"
                  target="_blank"
                  class="text-xs text-blue-600 hover:underline truncate max-w-[100px]"
                >
                  {{ __('Ver Instrumento') }}
                </a>
                <button
                  type="button"
                  class="text-ink-gray-4 hover:text-red-600 ml-1"
                  :title="__('Remover anexo')"
                  @click="removeAttachment(title)"
                >
                  <Icon icon="lucide-x" class="size-3" />
                </button>
              </div>

              <!-- Se requer anexo obrigatório e está sem anexo -->
              <div
                v-else-if="requiresAttachment(title.species)"
                class="p-1.5 border border-red-500 rounded bg-red-50/50 flex flex-col items-center gap-1"
              >
                <span class="text-[11px] text-red-600 font-medium">
                  {{ `Obrigatório para ${title.species}` }}
                </span>
                <Button
                  size="sm"
                  variant="subtle"
                  class="!h-6 !text-xs !px-2 bg-white border border-red-200 hover:bg-red-50"
                  :loading="uploadingTitle === title.name"
                  @click="openUploadDialog(title)"
                >
                  {{ __('Anexar') }}
                </Button>
              </div>

              <!-- Dispensado / Sem necessidade -->
              <span v-else class="text-xs text-ink-gray-4">
                {{ title.species ? '—' : '—' }}
              </span>
            </td>

            <!-- Status no Cartório -->
            <td class="py-3 px-3">
              <div class="flex flex-col gap-1">
                <!-- PROTESTADO -->
                <Badge
                  v-if="(title.protest_status || '').toUpperCase() === 'PROTESTADO'"
                  label="PROTESTADO"
                  theme="red"
                  variant="subtle"
                />

                <!-- DEVOLVIDO -->
                <template v-else-if="(title.protest_status || '').toUpperCase() === 'DEVOLVIDO'">
                  <Badge label="DEVOLVIDO" theme="red" variant="subtle" />
                  <span class="text-[11px] text-ink-gray-5">{{ __('See the reason in the card activity.') }}</span>
                  <Button
                    size="sm"
                    variant="subtle"
                    class="!h-6 !text-xs !px-2 mt-1"
                    @click="protestTitle(title)"
                  >
                    Reenviar
                  </Button>
                </template>

                <!-- Na CENPROT / no cartório (status oficiais do manual v2.2) -->
                <template v-else-if="IN_PROGRESS.includes(statusOf(title))">
                  <Badge :label="statusOf(title)" :theme="statusOf(title) === 'CONFIRMADO' ? 'orange' : 'blue'" variant="subtle" />
                  <span v-if="title.sent_at" class="text-[10px] text-ink-gray-5">
                    {{ __('Sent on {0}', [formatBrazilianDate(String(title.sent_at).slice(0, 10))]) }}
                  </span>
                </template>

                <!-- PAGO -->
                <Badge
                  v-else-if="(title.protest_status || '').toUpperCase() === 'PAGO'"
                  label="PAGO"
                  theme="green"
                  variant="subtle"
                />

                <!-- PENDENTE / EM ABERTO -->
                <Badge
                  v-else
                  :label="title.protest_status || 'Pendente'"
                  theme="gray"
                  variant="subtle"
                />

                <span
                  v-if="title.protest_protocol"
                  class="block text-[11px] text-ink-gray-5"
                >
                  Prot: {{ title.protest_protocol }}
                </span>
              </div>
            </td>

            <!-- Ações Rápidas -->
            <td class="py-3 px-3 text-center">
              <div class="flex flex-col items-center justify-center gap-1">
                <div class="flex items-center gap-1.5">
                  <!-- Botão 2ª Via WhatsApp -->
                  <Tooltip :text="__('Copiar linha digitável / 2ª via')">
                    <Button
                      size="sm"
                      variant="subtle"
                      iconLeft="lucide-copy"
                      @click="sendSecondCopy(title)"
                    >
                      2ª Via
                    </Button>
                  </Tooltip>

                  <!-- Botão Enviar / Protestar -->
                  <Button
                    size="sm"
                    variant="solid"
                    theme="blue"
                    :loading="loadingProtest === title.name"
                    :disabled="
                      loadingProtest === title.name ||
                      !title.species ||
                      (requiresAttachment(title.species) && !title.attachment) ||
                      !SENDABLE.includes(statusOf(title))
                    "
                    @click="protestTitle(title)"
                  >
                    Enviar
                  </Button>
                </div>
                <div v-if="title.sent_at" class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-[11px] text-ink-gray-6 hover:underline"
                    :disabled="loadingProtest === title.name"
                    @click="refreshTitle(title)"
                  >
                    {{ __('Update status') }}
                  </button>
                  <button
                    v-if="WITHDRAW_LABEL[statusOf(title)]"
                    type="button"
                    class="text-[11px] text-red-600 hover:underline"
                    :disabled="loadingProtest === title.name"
                    @click="confirmWithdraw(title)"
                  >
                    {{ __(WITHDRAW_LABEL[statusOf(title)]) }}
                  </button>
                </div>

                <!-- Mensagens de Validação Obrigatória em Vermelho Embaixo do Botão -->
                <span
                  v-if="!title.species"
                  class="text-[11px] text-red-600 font-medium"
                >
                  Selecione o título cartório
                </span>
                <span
                  v-else-if="requiresAttachment(title.species) && !title.attachment"
                  class="text-[11px] text-red-600 font-medium"
                >
                  {{ `Anexo obrigatório para ${title.species}` }}
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="flex flex-col items-center justify-center py-8 text-center border border-dashed border-outline-gray-3 rounded-lg"
    >
      <Icon icon="lucide-file-text" class="size-8 text-ink-gray-4 mb-2" />
      <span class="text-p-base font-medium text-ink-gray-8">
        {{ __('Nenhum título vencido registrado neste caso.') }}
      </span>
      <span class="text-p-sm text-ink-gray-5 mt-0.5">
        {{ __('Adicione manualmente ou importe a carteira via planilha / ERP.') }}
      </span>
      <Button
        class="mt-4"
        variant="solid"
        iconLeft="lucide-plus"
        :label="__('Adicionar Primeiro Título')"
        @click="showAddModal = true"
      />
    </div>

    <!-- Modal de Adicionar Título -->
    <Dialog v-model:open="showAddModal" :title="__('Adicionar Título de Cobrança')" size="lg">
      <template #default>
        <div class="grid grid-cols-2 gap-4 py-2">
          <FormControl
            v-model="newTitle.title_number"
            type="text"
            :label="__('Número do Título / Duplicata')"
            placeholder="ex: NF-10492"
            required
          />
          <FormControl
            v-model="newTitle.our_number"
            type="text"
            :label="__('Nosso Número')"
            placeholder="ex: 000123456"
          />
          <FormControl
            v-model="newTitle.species"
            type="select"
            :label="__('Espécie (Título Cartório)')"
            :options="speciesOptionsModal"
            required
          />
          <FormControl
            v-model="newTitle.issue_date"
            type="date"
            :label="__('Issue date')"
            required
          />
          <FormControl
            v-model="newTitle.due_date"
            type="date"
            :label="__('Data de Vencimento')"
            required
          />
          <FormControl
            v-model.number="newTitle.original_amount"
            type="number"
            :label="__('Valor Original (R$)')"
            required
          />
          <FormControl
            v-model.number="newTitle.updated_amount"
            type="number"
            :label="__('Valor Atualizado c/ Juros (R$)')"
          />
          <div class="col-span-2">
            <FormControl
              v-model="newTitle.digitable_line"
              type="text"
              :label="__('Linha Digitável / Código de Barras')"
              placeholder="34191.79001 01043.510047 91020.150008 8 98760000015000"
            />
          </div>
          <div
            v-if="requiresAttachment(newTitle.species)"
            class="col-span-2 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700"
          >
            <strong>Atenção:</strong> A espécie {{ newTitle.species }} exige o anexo digital do instrumento (PDF assinado) para protesto no cartório.
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancelar')" @click="showAddModal = false" />
          <Button
            variant="solid"
            :label="__('Salvar Título')"
            :disabled="!newTitle.title_number || !newTitle.species || !newTitle.due_date || !newTitle.original_amount"
            @click="saveNewTitle"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Badge, Button, Dialog, FormControl, Tooltip, call, toast } from 'frappe-ui'
import { createDialog } from '@/utils/dialogs'
import Icon from '@/components/Icon.vue'

const props = defineProps({
  deal: { type: Object, required: true },
})

const emit = defineEmits(['reload', 'sendWhatsapp'])

const showAddModal = ref(false)
const loadingProtest = ref(null)
const uploadingTitle = ref(null)
const fileInputRef = ref(null)
const targetTitleForUpload = ref(null)

const titles = computed(() => {
  return props.deal.titles || []
})

const totalAmount = computed(() => {
  return titles.value.reduce((sum, t) => sum + Number(t.updated_amount || t.original_amount || 0), 0)
})

// Opções completas de espécies de cartório (CENPROT)
const speciesOptions = [
  { label: 'DMI - Duplicata de Venda Mercantil por Indicação', value: 'DMI' },
  { label: 'DSI - Duplicata de Prestação de Serviços por Indicação', value: 'DSI' },
  { label: 'CBI - Cédula de Crédito Bancário por Indicação', value: 'CBI' },
  { label: 'CT - Espécie de Contrato', value: 'CT' },
  { label: 'NP - Nota Promissória', value: 'NP' },
  { label: 'CCB - Cédula de Crédito Bancário (Física)', value: 'CCB' },
  { label: 'DM - Duplicata Mercantil (Física)', value: 'DM' },
  { label: 'DS - Duplicata de Serviço (Física)', value: 'DS' },
  { label: 'CH - Cheque', value: 'CH' },
  { label: 'CD - Confissão de Dívida', value: 'CD' },
  { label: 'CPS - Conta de Prestação de Serviços', value: 'CPS' },
]

const speciesOptionsModal = [
  { label: 'Selecionar espécie...', value: '' },
  ...speciesOptions
]

const newTitle = ref({
  title_number: '',
  our_number: '',
  species: '',
  issue_date: '',
  due_date: '',
  original_amount: 0,
  updated_amount: 0,
  digitable_line: '',
  attachment: '',
})

// Status da CENPROT (manual v2.2). Texto que não é status da CENPROT (ex.: "Pendente" da importação) = não enviado
const CENPROT_STATUSES = ['INEXISTENTE', 'COLETADO', 'GERADO', 'AGENDADO', 'ENVIADO', 'CONFIRMADO', 'DEVOLVIDO', 'CANCELADO', 'PAGO', 'PROTESTADO', 'RETIRADO', 'SUSTADO', 'SUSPENSO']
const SENDABLE = ['', 'INEXISTENTE', 'DEVOLVIDO']
const IN_PROGRESS = ['COLETADO', 'GERADO', 'AGENDADO', 'ENVIADO', 'CONFIRMADO']
// Operação permitida em cada status: remoção antes do cartório, desistência no cartório, cancelamento protestado
const WITHDRAW_LABEL = {
  COLETADO: 'Cancel sending',
  GERADO: 'Cancel sending',
  CONFIRMADO: 'Withdraw from the registry',
  PROTESTADO: 'Cancel the protest',
}

function statusOf(title) {
  const status = (title.protest_status || '').trim().toUpperCase()
  return CENPROT_STATUSES.includes(status) ? status : ''
}

// Espécies que exigem o PDF/documento assinado anexado
function requiresAttachment(species) {
  if (!species) return false
  return ['CT', 'NP', 'CCB', 'DM', 'DS', 'CH', 'CD', 'CPS', 'CA', 'CL', 'CM', 'TA'].includes(species.toUpperCase())
}

// Formatação brasileira de data: dd mmm aaaa (ex: "21 Out 2026")
function formatBrazilianDate(dateStr) {
  if (!dateStr) return '—'
  const parts = String(dateStr).split('-')
  if (parts.length === 3) {
    const day = parts[2].padStart(2, '0')
    const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    const mIdx = parseInt(parts[1], 10) - 1
    const month = months[mIdx] || parts[1]
    const year = parts[0]
    return `${day} ${month} ${year}`
  }
  return dateStr
}

function daysOverdue(dueDate) {
  if (!dueDate) return 0
  const diff = new Date().getTime() - new Date(dueDate).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  return days > 0 ? days : 0
}

function formatMoney(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value || 0))
}

// Atualização de espécie no dropdown
async function onSpeciesChange(title, newSpecies) {
  title.species = newSpecies
  title.requires_attachment = requiresAttachment(newSpecies) ? 1 : 0

  try {
    if (title.name) {
      await call('frappe.client.set_value', {
        doctype: 'CRM Deal Title',
        name: title.name,
        fieldname: {
          species: newSpecies,
          requires_attachment: title.requires_attachment,
        },
      })
    } else {
      await saveAllTitles()
    }
    toast.success(__('Espécie de cartório atualizada!'))
  } catch (err) {
    toast.error(err.message || __('Erro ao atualizar espécie.'))
  }
}

// Upload de anexo
function openUploadDialog(title) {
  targetTitleForUpload.value = title
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
    fileInputRef.value.click()
  }
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file || !targetTitleForUpload.value) return

  const title = targetTitleForUpload.value
  uploadingTitle.value = title.name || true

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('is_private', '1')
    formData.append('doctype', 'CRM Deal Title')
    formData.append('docname', title.name || '')

    const response = await fetch('/api/method/upload_file', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Frappe-CSRF-Token': window.frappe?.csrf_token || '',
      },
    })
    const data = await response.json()
    const fileUrl = data.message?.file_url

    if (fileUrl) {
      title.attachment = fileUrl
      if (title.name) {
        await call('frappe.client.set_value', {
          doctype: 'CRM Deal Title',
          name: title.name,
          fieldname: 'attachment',
          value: fileUrl,
        })
      } else {
        await saveAllTitles()
      }
      toast.success(__('Instrumento anexado com sucesso!'))
    } else {
      throw new Error(data.message || __('Falha ao fazer upload do arquivo.'))
    }
  } catch (err) {
    toast.error(err.message || __('Erro no envio do documento.'))
  } finally {
    uploadingTitle.value = null
    targetTitleForUpload.value = null
  }
}

async function removeAttachment(title) {
  title.attachment = ''
  try {
    if (title.name) {
      await call('frappe.client.set_value', {
        doctype: 'CRM Deal Title',
        name: title.name,
        fieldname: 'attachment',
        value: '',
      })
    } else {
      await saveAllTitles()
    }
    toast.success(__('Anexo removido.'))
  } catch (err) {
    toast.error(err.message || __('Erro ao remover anexo.'))
  }
}

function sendSecondCopy(title) {
  if (title.digitable_line) {
    navigator.clipboard.writeText(title.digitable_line)
    toast.success(__('Linha digitável copiada!'))
    emit('sendWhatsapp', `Olá! Segue a linha digitável do título ${title.title_number}: ${title.digitable_line}`)
  } else {
    toast.warning(__('Este título não possui linha digitável cadastrada.'))
  }
}

async function protestTitle(title) {
  if (!title.species) {
    toast.error(__('Selecione o tipo de título em cartório antes de protestar.'))
    return
  }
  if (requiresAttachment(title.species) && !title.attachment) {
    toast.error(__('Esta espécie exige o anexo do documento assinado (PDF) antes de protestar.'))
    return
  }

  createDialog({
    title: __('Send to protest'),
    message: __('Title {0} goes to CENPROT now, in the name of the creditor of the settings. Registry fees may apply.', [title.title_number]),
    size: 'md',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Send to protest'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          runTitle(title, 'send_row')
        },
      },
    ],
  })
}

// Envia, consulta ou retira um título; o status novo sempre vem do servidor (CENPROT)
async function runTitle(title, method, extra = {}) {
  loadingProtest.value = title.name
  try {
    const res = await call('cred_hub.integrations.protest.' + method, {
      deal: props.deal.name,
      title_row: title.name,
      ...extra,
    })
    if (res.ok) {
      toast.success(res.message || __('Done.'))
    } else {
      toast.error(res.message || __('CENPROT did not accept the request.'))
    }
    emit('reload')
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Could not reach CENPROT.'))
  } finally {
    loadingProtest.value = null
  }
}

function refreshTitle(title) {
  runTitle(title, 'refresh_row')
}

function confirmWithdraw(title) {
  const label = __(WITHDRAW_LABEL[statusOf(title)])
  createDialog({
    title: label,
    message: __('CENPROT receives the request for title {0} now. The status changes only when CENPROT confirms it.', [title.title_number]),
    size: 'md',
    actions: [
      { label: __('Back'), onClick: ({ close }) => close() },
      {
        label,
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }) => {
          close()
          runTitle(title, 'withdraw_row', { justification: __('Requested by the operator in HubTech') })
        },
      },
    ],
  })
}

async function saveAllTitles() {
  await call('frappe.client.set_value', {
    doctype: 'CRM Deal',
    name: props.deal.name,
    fieldname: 'titles',
    value: props.deal.titles,
  })
}

async function saveNewTitle() {
  const t = newTitle.value
  if (!t.title_number || !t.species || !t.issue_date || !t.due_date || !t.original_amount) {
    toast.error(__('Fill number, species, issue date, due date and amount.'))
    return
  }

  const row = {
    ...newTitle.value,
    updated_amount: newTitle.value.updated_amount || newTitle.value.original_amount,
    requires_attachment: requiresAttachment(newTitle.value.species) ? 1 : 0,
    protest_status: 'Pendente',
  }

  try {
    const currentTitles = [...(props.deal.titles || []), row]
    await call('frappe.client.set_value', {
      doctype: 'CRM Deal',
      name: props.deal.name,
      fieldname: 'titles',
      value: currentTitles,
    })
    toast.success(__('Título adicionado com sucesso!'))
    showAddModal.value = false
    emit('reload')
  } catch (err) {
    toast.error(err.message || __('Erro ao salvar o título.'))
  }
}
</script>
