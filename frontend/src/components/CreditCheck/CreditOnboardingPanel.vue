<template>
  <div class="space-y-6">
    <!-- 1. Pasta Digital de Crédito (Checklist de Documentos) -->
    <div
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="text-base font-semibold text-[#1E1F23]">
              {{ __('Pasta Digital · Checklist de Documentos') }}
            </span>
            <span
              v-if="summary"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border"
              :class="
                summary.all_required_verified
                  ? 'bg-[#E7F6EC] text-[#1F7A3D] border-[#A6F4C5]'
                  : 'bg-[#E5F1FF] text-[#0088FF] border-[#B2D7FF]'
              "
            >
              {{
                summary.all_required_verified
                  ? __('Obrigatórios conferidos ✓')
                  : __('{0}/{1} obrigatórios conferidos', [
                      summary.required_verified_count,
                      summary.required_total,
                    ])
              }}
            </span>
          </div>
          <p class="text-xs text-[#5E6068] mt-0.5">
            {{
              __(
                'Anexe os documentos ou envie o Link Seguro (Caixa de Correio Blindada) para o cliente/contador anexar direto na pasta.',
              )
            }}
          </p>
        </div>
        <div v-if="summary" class="text-right">
          <span class="text-xs font-semibold text-[#1E1F23]">
            {{
              __('{0} de {1} documentos conferidos ({2}%)', [
                summary.verified_count,
                summary.total,
                summary.progress_percent,
              ])
            }}
          </span>
        </div>
      </div>

      <!-- Progress bar -->
      <div
        v-if="summary"
        class="w-full h-2 bg-surface-gray-2 rounded-full overflow-hidden"
      >
        <div
          class="h-full transition-all duration-300 rounded-full"
          :class="
            summary.all_required_verified
              ? 'bg-surface-green-3'
              : 'bg-surface-blue-3'
          "
          :style="{ width: `${summary.progress_percent}%` }"
        />
      </div>

      <!-- Link Externo Blindado (Caixa de Correio para o Cliente / Contador) -->
      <div
        class="p-3.5 rounded-lg bg-surface-gray-1 border border-outline-gray-2 flex flex-wrap items-center justify-between gap-3"
      >
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <span class="text-p-sm font-semibold text-ink-gray-9">
              🔒 {{ __('Link Externo para Cliente / Contador (Só Envio · Protegido por CNPJ)') }}
            </span>
            <Badge
              v-if="portal.active"
              theme="green"
              variant="subtle"
              size="sm"
            >
              {{ __('Ativo até {0}', [portal.expires_on]) }}
            </Badge>
          </div>
          <p v-if="!portal.active" class="text-xs text-ink-gray-6 mt-0.5">
            {{
              __(
                'Gera um link protegido pelo CNPJ onde o cliente ou contador sobe os documentos direto para este Card, sem conseguir baixar nem ver arquivos já enviados.',
              )
            }}
          </p>
          <div
            v-else
            class="mt-1.5 flex flex-wrap items-center gap-2 text-p-sm"
          >
            <input
              type="text"
              readonly
              :value="portalFullUrl"
              class="flex-1 min-w-[240px] rounded border border-outline-gray-2 bg-surface-white px-2.5 py-1 text-xs text-ink-gray-8"
              @focus="$event.target.select()"
            />
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2 shrink-0">
          <Button
            v-if="!portal.active"
            variant="outline"
            size="sm"
            :loading="generatingLink"
            @click="generateLink(false)"
          >
            {{ __('Gerar Link para Cliente') }}
          </Button>
          <template v-else>
            <Button variant="solid" size="sm" @click="copyPortalLink">
              {{ __('Copiar Link') }}
            </Button>
            <Button
              variant="outline"
              size="sm"
              :loading="loadingWhatsapp"
              @click="sendWhatsappReminder"
            >
              📲 {{ __('Cobrar via WhatsApp') }}
            </Button>
            <a
              v-if="portalFullUrl"
              :href="portalFullUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded border border-outline-gray-2 bg-surface-white text-ink-gray-8 hover:bg-surface-gray-2"
            >
              {{ __('Abrir ↗') }}
            </a>
            <Button
              variant="ghost"
              size="sm"
              :loading="generatingLink"
              @click="revokeLink"
            >
              {{ __('Desativar') }}
            </Button>
          </template>
        </div>
      </div>

      <!-- Checklist items -->
      <div v-if="checklist.length" class="space-y-2.5 pt-1">
        <div
          v-for="item in checklist"
          :key="item.key"
          class="p-3.5 rounded-lg border border-[#E6E7EB] bg-white hover:border-[#DCDDE2] transition-colors space-y-2"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="flex items-start gap-3 min-w-0 flex-1">
              <!-- Quick check button -->
              <button
                type="button"
                class="mt-0.5 size-5 rounded border flex items-center justify-center shrink-0 transition-colors"
                :class="
                  item.status === 'verified'
                    ? 'bg-[#1F7A3D] border-[#1F7A3D] text-white'
                    : 'border-[#DCDDE2] bg-white hover:border-[#5E6068]'
                "
                :title="
                  item.status === 'verified'
                    ? __('Desmarcar conferência')
                    : __('Marcar como Conferido ✓')
                "
                :disabled="savingKey === item.key"
                @click="toggleVerified(item)"
              >
                <span v-if="item.status === 'verified'" class="text-xs font-bold"
                  >✓</span
                >
              </button>

              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span
                    class="text-sm font-semibold"
                    :class="
                      item.status === 'verified'
                        ? 'text-[#1E1F23]'
                        : 'text-[#2A2B30]'
                    "
                  >
                    {{ item.label }}
                  </span>
                  <span
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-[#F5F5F7] text-[#5E6068] border border-[#E6E7EB]"
                  >
                    {{ item.category }}
                  </span>
                  <span
                    v-if="item.required"
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]"
                  >
                    {{ __('Obrigatório') }}
                  </span>
                  <span
                    v-if="item.is_expired"
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA]"
                  >
                    ⏰ {{ __('Vencido ({0})', [item.valid_until]) }}
                  </span>
                  <span
                    v-else-if="item.expiring_soon"
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-[#FFF4D6] text-[#8A5A00] border border-[#FEEA9F]"
                  >
                    ⏰ {{ __('Vence em {0}', [item.valid_until]) }}
                  </span>
                  <span
                    v-else-if="item.valid_until"
                    class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-[#F5F5F7] text-[#5E6068] border border-[#E6E7EB]"
                  >
                    📅 {{ __('Validade: {0}', [item.valid_until]) }}
                  </span>
                </div>

                <!-- File link, Expiration Input & Smart Extraction -->
                <div class="flex flex-wrap items-center gap-3 mt-1.5 text-xs">
                  <a
                    v-if="item.file_url"
                    :href="item.file_url"
                    target="_blank"
                    class="text-[#0088FF] hover:underline font-medium truncate max-w-xs inline-flex items-center gap-1"
                  >
                    📎 {{ item.file_name || __('Ver documento anexado') }}
                  </a>
                  <span v-else class="text-[#8A8C94]">
                    {{ __('Nenhum arquivo anexado') }}
                  </span>
                  <span v-if="item.updated_on" class="text-xs text-[#8A8C94]">
                    · {{ item.updated_on }}
                  </span>
                  <label
                    class="inline-flex items-center gap-1.5 text-xs text-[#5E6068] ml-auto"
                    :title="__('Data de vencimento do documento (se aplicável)')"
                  >
                    <span>{{ __('Vencimento:') }}</span>
                    <input
                      type="date"
                      :value="item.valid_until || ''"
                      class="rounded border border-[#DCDDE2] bg-[#F5F5F7] px-1.5 py-0.5 text-xs text-[#1E1F23] focus:bg-white focus:border-[#0088FF]"
                      @change="onValidUntilChange(item, $event.target.value)"
                    />
                  </label>
                </div>

                <!-- Extracted Smart Data Pill -->
                <div
                  v-if="item.extracted_data && item.extracted_data.summary_text"
                  class="mt-1.5 text-xs text-[#0088FF] bg-[#E5F1FF] border border-[#B2D7FF] px-2.5 py-1.5 rounded flex items-center justify-between gap-2"
                >
                  <span>✨ {{ item.extracted_data.summary_text }}</span>
                </div>

                <!-- Callout de Alerta da IA (Risco de Rejeição Sugerido) -->
                <div
                  v-if="item.extracted_data && item.extracted_data.rejection_risk && item.status !== 'rejected'"
                  class="mt-1.5 text-xs bg-[#FFF4D6] text-[#8A5A00] border border-[#FEEA9F] px-2.5 py-1.5 rounded flex flex-wrap items-center justify-between gap-2"
                >
                  <span class="font-medium min-w-0 flex-1">
                    ⚠️ <strong>{{ __('IA') }}:</strong> {{ item.extracted_data.suggested_reason || item.extracted_data.summary_text }}
                  </span>
                  <Button
                    variant="outline"
                    theme="red"
                    size="sm"
                    class="shrink-0 text-xs py-0.5 h-6 bg-white hover:bg-[#FEF3F2]"
                    @click="openRejectModal(item, item.extracted_data.suggested_reason)"
                  >
                    {{ __('Recusar com motivo da IA') }}
                  </Button>
                </div>

                <!-- Callout de Documento Recusado -->
                <div
                  v-if="item.status === 'rejected'"
                  class="mt-1.5 text-xs bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA] px-3 py-2 rounded flex items-start justify-between gap-2"
                >
                  <div class="space-y-0.5 min-w-0 flex-1">
                    <span class="font-semibold">{{ __('Documento Recusado') }}:</span>
                    <span class="ml-1">{{ item.notes || __('Aguardando reenvio pelo cliente.') }}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-[#B42318] hover:bg-[#FEE4E2] shrink-0 text-xs h-6 px-2"
                    @click="openRejectModal(item)"
                  >
                    {{ __('Alterar motivo') }}
                  </Button>
                </div>

                <div
                  v-if="item.notes && editingNoteKey !== item.key"
                  class="mt-1 text-xs text-[#5E6068] bg-[#F5F5F7] px-2.5 py-1 rounded border border-[#E6E7EB]"
                >
                  💬 {{ item.notes }}
                </div>
              </div>
            </div>

            <!-- Status & Actions -->
            <div class="flex flex-wrap items-center gap-2 shrink-0">
              <span
                class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border"
                :class="
                  item.status === 'verified'
                    ? 'bg-[#E7F6EC] text-[#1F7A3D] border-[#A6F4C5] font-semibold'
                    : item.status === 'rejected'
                      ? 'bg-[#FEF3F2] text-[#B42318] border-[#FECDCA] font-semibold'
                      : 'bg-[#F5F5F7] text-[#5E6068] border-[#E6E7EB]'
                "
              >
                {{ statusLabel(item.status) }}
              </span>

              <FileUploader
                :doctype="targetDoctype"
                :docname="targetDocname"
                private
                @success="(file) => onFileUploaded(item, file)"
              >
                <template #default="{ openFileSelector, uploading }">
                  <Button
                    variant="outline"
                    size="sm"
                    :loading="uploading || savingKey === item.key"
                    @click="openFileSelector()"
                  >
                    {{ item.file_url ? __('Trocar') : __('Anexar') }}
                  </Button>
                </template>
              </FileUploader>

              <Button
                v-if="item.file_url"
                variant="ghost"
                size="sm"
                :loading="analyzingKey === item.key"
                :title="__('Extrair números e indicadores automaticamente do arquivo anexado')"
                @click="analyzeDocument(item)"
              >
                ✨ {{ __('Extrair dados') }}
              </Button>

              <Button
                v-if="item.status !== 'verified'"
                variant="subtle"
                theme="green"
                size="sm"
                :loading="savingKey === item.key"
                @click="markStatus(item, 'verified')"
              >
                {{ __('Conferir ✓') }}
              </Button>

              <Button
                v-if="item.file_url && item.status !== 'rejected'"
                variant="subtle"
                theme="red"
                size="sm"
                :loading="savingKey === item.key"
                @click="openRejectModal(item)"
              >
                {{ __('Recusar ✕') }}
              </Button>

              <Button
                variant="ghost"
                size="sm"
                @click="openNoteEditor(item)"
              >
                {{ item.notes ? __('Editar nota') : __('Nota interna') }}
              </Button>

              <button
                v-if="item.is_custom"
                type="button"
                class="text-[#B42318] hover:text-[#912018] text-xs font-bold px-1"
                :title="__('Remover documento específico')"
                @click="removeCustomItem(item.key)"
              >
                ✕
              </button>
            </div>
          </div>

          <!-- Inline note / rejection editor -->
          <div
            v-if="editingNoteKey === item.key"
            class="pl-8 pt-2 space-y-2 bg-surface-gray-1 p-3 rounded-lg"
          >
            <FormControl
              v-model="noteDraft"
              type="text"
              :label="__('Observação ou motivo de pendência/rejeição')"
              :placeholder="
                __('Ex: Falta assinatura do contador ou documento ilegível')
              "
            />
            <div class="flex flex-wrap items-center gap-2">
              <Button
                variant="solid"
                size="sm"
                :loading="savingKey === item.key"
                @click="saveNoteAndStatus(item, item.status)"
              >
                {{ __('Salvar observação') }}
              </Button>
              <Button
                variant="outline"
                theme="red"
                size="sm"
                :loading="savingKey === item.key"
                @click="saveNoteAndStatus(item, 'rejected')"
              >
                {{ __('Marcar como Rejeitado / Pedir reenvio') }}
              </Button>
              <Button
                v-if="item.status !== 'pending'"
                variant="subtle"
                size="sm"
                :loading="savingKey === item.key"
                @click="saveNoteAndStatus(item, 'pending')"
              >
                {{ __('Voltar para Pendente') }}
              </Button>
              <Button variant="ghost" size="sm" @click="editingNoteKey = ''">
                {{ __('Cancelar') }}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- Adicionar documento específico para este cliente/card -->
      <div class="pt-2 border-t border-outline-gray-1">
        <div v-if="!showAddCustom" class="flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            @click="showAddCustom = true"
          >
            + {{ __('Solicitar documento específico neste cliente/card') }}
          </Button>
        </div>
        <div
          v-else
          class="p-3 bg-surface-gray-1 rounded-lg flex flex-wrap items-end gap-3"
        >
          <FormControl
            v-model="customDocLabel"
            type="text"
            class="flex-1 min-w-[220px]"
            :label="__('Nome do documento específico')"
            :placeholder="__('Ex: Matrícula do Imóvel em Garantia')"
          />
          <FormControl
            v-model="customDocCategory"
            type="select"
            :label="__('Categoria')"
            :options="[
              { label: __('Garantia / Lastro'), value: 'Lastro' },
              { label: __('Financeiro'), value: 'Financeiro' },
              { label: __('Societário'), value: 'Societário' },
              { label: __('Operacional'), value: 'Operacional' },
            ]"
          />
          <div class="flex items-center gap-2 pb-1">
            <Button
              variant="solid"
              size="sm"
              :loading="addingCustom"
              @click="addCustomItem"
            >
              {{ __('Adicionar à pasta') }}
            </Button>
            <Button variant="ghost" size="sm" @click="showAddCustom = false">
              {{ __('Cancelar') }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. Relatório de Visita Técnica / Comercial (In loco) -->
    <div
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Relatório de Visita ao Cedente / Cliente') }}
            </span>
            <Badge :theme="visitStatusTheme" variant="subtle">
              {{ visitStatusLabel }}
            </Badge>
            <Badge
              v-if="visit.status === 'completed'"
              :theme="visitRecTheme"
              variant="solid"
            >
              {{ visitRecLabel }}
            </Badge>
          </div>
          <p class="text-p-sm text-ink-gray-6 mt-0.5">
            {{
              __(
                'Registro estruturado da visita técnica/comercial (estrutura física, estoque, quadro de funcionários e fotos). Entra automaticamente no Parecer de Crédito da IA.',
              )
            }}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          @click="showVisitForm = !showVisitForm"
        >
          {{
            showVisitForm
              ? __('Recolher formulário')
              : visit.status === 'not_done'
                ? __('Registrar Visita')
                : __('Editar Visita')
          }}
        </Button>
      </div>

      <!-- Compact Summary when completed/scheduled and form is collapsed -->
      <div
        v-if="!showVisitForm && visit.status !== 'not_done'"
        class="p-4 bg-surface-gray-1 rounded-lg border border-outline-gray-2 space-y-2 text-p-sm"
      >
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div>
            <span class="text-ink-gray-5">{{ __('Data da visita:') }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ visit.visit_date || '—' }}
            </div>
          </div>
          <div>
            <span class="text-ink-gray-5">{{ __('Responsável:') }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ visit.visitor_name || '—' }}
            </div>
          </div>
          <div>
            <span class="text-ink-gray-5">{{ __('Modalidade / Sede:') }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ visitTypeLabel(visit.visit_type) }} ·
              {{ propertyTypeLabel(visit.property_type) }}
            </div>
          </div>
          <div>
            <span class="text-ink-gray-5">{{ __('Operação observada:') }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ operationalLabel(visit.operational_status) }}
            </div>
          </div>
          <div>
            <span class="text-ink-gray-5">{{ __('Estoque / Produção:') }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ inventoryLabel(visit.inventory_level) }}
            </div>
          </div>
          <div>
            <span class="text-ink-gray-5">{{
              __('Funcionários observados:')
            }}</span>
            <div class="font-medium text-ink-gray-9">
              {{ visit.employees_observed || '—' }}
            </div>
          </div>
        </div>
        <div v-if="visit.notes" class="pt-2 border-t border-outline-gray-2">
          <span class="text-ink-gray-5">{{
            __('Observações do visitador:')
          }}</span>
          <p class="text-ink-gray-8 whitespace-pre-line mt-0.5">
            {{ visit.notes }}
          </p>
        </div>
        <div
          v-if="visit.photos && visit.photos.length"
          class="pt-2 border-t border-outline-gray-2 flex flex-wrap gap-3"
        >
          <a
            v-for="(photo, idx) in visit.photos"
            :key="idx"
            :href="photo.file_url"
            target="_blank"
            class="text-ink-blue-3 underline font-medium"
          >
            📷 {{ photo.file_name }}
          </a>
        </div>
      </div>

      <!-- Expandable Visit Form -->
      <div
        v-if="showVisitForm"
        class="space-y-4 pt-2 border-t border-outline-gray-2"
      >
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormControl
            v-model="visitDraft.status"
            type="select"
            :label="__('Situação da visita')"
            :options="[
              { label: __('Realizada'), value: 'completed' },
              { label: __('Agendada'), value: 'scheduled' },
              { label: __('Não realizada'), value: 'not_done' },
            ]"
          />
          <FormControl
            v-model="visitDraft.visit_date"
            type="date"
            :label="__('Data da visita')"
          />
          <FormControl
            v-model="visitDraft.visitor_name"
            type="text"
            :label="__('Visitador / Analista responsável')"
            :placeholder="__('Nome de quem realizou a visita')"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormControl
            v-model="visitDraft.visit_type"
            type="select"
            :label="__('Modalidade da visita')"
            :options="[
              { label: __('Presencial (in loco)'), value: 'presencial' },
              { label: __('Vídeo / Remota'), value: 'video' },
              { label: __('Vistoria Terceirizada'), value: 'terceirizada' },
            ]"
          />
          <FormControl
            v-model="visitDraft.property_type"
            type="select"
            :label="__('Tipo de imóvel / sede')"
            :options="[
              { label: __('Imóvel Próprio'), value: 'proprio' },
              { label: __('Imóvel Alugado'), value: 'alugado' },
              { label: __('Cedido / Condomínio'), value: 'cedido' },
            ]"
          />
          <FormControl
            v-model="visitDraft.employees_observed"
            type="text"
            :label="__('Funcionários observados no local')"
            :placeholder="__('Ex: ~30 na produção e 5 no escritório')"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormControl
            v-model="visitDraft.operational_status"
            type="select"
            :label="__('Atividade e estrutura operacional')"
            :options="[
              {
                label: __('Plena atividade / Boa estrutura'),
                value: 'otimo',
              },
              { label: __('Operação regular'), value: 'regular' },
              {
                label: __('Estrutura precária / Baixa movimentação'),
                value: 'precario',
              },
              {
                label: __('Incompatível com o faturamento declarado'),
                value: 'incompativel',
              },
            ]"
          />
          <FormControl
            v-model="visitDraft.inventory_level"
            type="select"
            :label="__('Nível de estoque / produção')"
            :options="[
              { label: __('Estoque / Produção alta'), value: 'alto' },
              { label: __('Normal / Compatível'), value: 'normal' },
              { label: __('Estoque baixo'), value: 'baixo' },
              {
                label: __('Prestação de serviços / Não aplicável'),
                value: 'servicos',
              },
            ]"
          />
          <FormControl
            v-model="visitDraft.recommendation"
            type="select"
            :label="__('Parecer do visitador')"
            :options="[
              { label: __('Favorável'), value: 'favoravel' },
              {
                label: __('Favorável com ressalvas'),
                value: 'ressalvas',
              },
              { label: __('Desfavorável'), value: 'desfavoravel' },
            ]"
          />
        </div>

        <FormControl
          v-model="visitDraft.notes"
          type="textarea"
          :rows="4"
          :label="__('Relato detalhado da visita')"
          :placeholder="
            __(
              'Descreva maquinário, movimentação vista no local, principais clientes (sacados) e fornecedores citados, histórico dos sócios e eventuais pontos de atenção...',
            )
          "
        />

        <!-- Visit Photos / Attachments -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-p-sm font-medium text-ink-gray-7">
              {{ __('Fotos da fachada, estoque, maquinário ou termo de visita') }}
            </span>
            <FileUploader
              :doctype="targetDoctype"
              :docname="targetDocname"
              private
              @success="onVisitPhotoUploaded"
            >
              <template #default="{ openFileSelector, uploading }">
                <Button
                  variant="outline"
                  size="sm"
                  :loading="uploading"
                  @click="openFileSelector()"
                >
                  📷 {{ __('Anexar foto / evidência') }}
                </Button>
              </template>
            </FileUploader>
          </div>
          <div
            v-if="visitDraft.photos && visitDraft.photos.length"
            class="flex flex-wrap gap-2"
          >
            <div
              v-for="(photo, index) in visitDraft.photos"
              :key="index"
              class="flex items-center gap-2 px-3 py-1.5 bg-surface-gray-2 rounded border border-outline-gray-2 text-p-sm"
            >
              <a
                :href="photo.file_url"
                target="_blank"
                class="text-ink-blue-3 underline truncate max-w-xs"
              >
                {{ photo.file_name }}
              </a>
              <button
                type="button"
                class="text-ink-red-3 hover:text-ink-red-4 text-xs font-bold"
                @click="removeVisitPhoto(index)"
              >
                ✕
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 pt-2">
          <Button
            variant="solid"
            :loading="savingVisit"
            @click="saveVisit"
          >
            {{ __('Salvar Relatório de Visita') }}
          </Button>
          <Button variant="subtle" @click="showVisitForm = false">
            {{ __('Cancelar') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- 3. Rating Interno (AA–E), Calculadora de Limite Sugerido, Grupo Econômico & Mesa de Comitê -->
    <div
      v-if="committee"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Rating Interno (AA–E), Limite Sugerido & Mesa de Comitê') }}
            </span>
            <Badge
              :theme="ratingTheme(committee.rating?.rating)"
              variant="solid"
            >
              {{ __('Rating {0} · {1}/1000 pts', [committee.rating?.rating || 'C', committee.rating?.score || 0]) }}
            </Badge>
            <Badge
              :theme="committeeStatusTheme(committee.status)"
              variant="subtle"
            >
              {{ committeeStatusLabel(committee.status) }}
            </Badge>
            <Badge
              v-if="committee.is_expired"
              theme="red"
              variant="solid"
            >
              ⏰ {{ __('Limite Vencido ({0})', [committee.valid_until]) }}
            </Badge>
            <Badge
              v-else-if="committee.expiring_soon"
              theme="amber"
              variant="subtle"
            >
              ⏰ {{ __('Limite vence em {0}', [committee.valid_until]) }}
            </Badge>
          </div>
          <p class="text-p-sm text-ink-gray-6 mt-0.5">
            {{
              __(
                'Score ponderado pelos 5 Cs do Crédito (Restritivos, Endividamento SCR, Maturidade/Capital, Bureau Score e Pasta Digital/Visita) + Alçada de Votação.',
              )
            }}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          @click="showCommitteeForm = !showCommitteeForm"
        >
          {{
            showCommitteeForm
              ? __('Recolher Mesa de Comitê')
              : __('Configurar Alçada / Votar')
          }}
        </Button>
      </div>

      <!-- KPI Cards: Limite Sugerido, Concentração por Sacado, Faturamento Base, Limite Aprovado -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="p-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2">
          <div class="text-xs text-ink-gray-6">
            {{ __('Limite Operacional Sugerido') }}
          </div>
          <div class="text-base font-semibold text-ink-gray-9 mt-0.5">
            {{ formatBRL(committee.rating?.suggested_limit || 0) }}
          </div>
          <div class="text-xs text-ink-gray-5 mt-0.5">
            {{ __('{0}% do faturamento mensal', [Math.round((committee.rating?.multiplier_applied || 0) * 100)]) }}
          </div>
        </div>
        <div class="p-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2">
          <div class="text-xs text-ink-gray-6">
            {{ __('Concentração Máx. por Sacado') }}
          </div>
          <div class="text-base font-semibold text-ink-gray-9 mt-0.5">
            {{ formatBRL(committee.rating?.suggested_max_concentration || 0) }}
          </div>
          <div class="text-xs text-ink-gray-5 mt-0.5">
            {{ __('Teto individual por CNPJ sacado') }}
          </div>
        </div>
        <div class="p-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2">
          <div class="text-xs text-ink-gray-6">
            {{ __('Faturamento Mensal Base') }}
          </div>
          <div class="text-base font-semibold text-ink-gray-9 mt-0.5">
            {{ formatBRL(committee.rating?.monthly_revenue_base || 0) }}
          </div>
          <div class="text-xs text-ink-gray-5 mt-0.5">
            {{ __('Extraído da Pasta ou Cadastro') }}
          </div>
        </div>
        <div class="p-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2">
          <div class="text-xs text-ink-gray-6">
            {{ __('Limite Aprovado em Comitê') }}
          </div>
          <div class="text-base font-semibold text-ink-green-3 mt-0.5">
            {{ committee.approved_limit ? formatBRL(committee.approved_limit) : '—' }}
          </div>
          <div class="text-xs text-ink-gray-5 mt-0.5">
            {{
              committee.valid_until
                ? __('Vigência até {0}', [committee.valid_until])
                : __('Quórum: {0}/{1} votos', [committee.approve_count || 0, committee.required_quorum || 1])
            }}
          </div>
        </div>
      </div>

      <!-- Breakdown dos Fatores do Rating -->
      <div
        v-if="committee.rating?.factors?.length"
        class="p-3 rounded-lg bg-surface-gray-1 border border-outline-gray-2 space-y-1.5"
      >
        <div class="text-xs font-semibold text-ink-gray-8 uppercase tracking-wide">
          {{ __('Memória de Cálculo do Rating ({0})', [committee.rating.rating_label]) }}
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-1.5 text-xs">
          <div
            v-for="(f, idx) in committee.rating.factors"
            :key="idx"
            class="flex items-center justify-between gap-2 bg-surface-white px-2.5 py-1 rounded border border-outline-gray-1"
          >
            <span class="text-ink-gray-7 truncate">{{ f.factor }}</span>
            <span
              class="font-semibold shrink-0"
              :class="f.impact >= 0 ? 'text-ink-green-3' : 'text-ink-red-3'"
            >
              {{ f.impact >= 0 ? `+${f.impact}` : f.impact }} pts
            </span>
          </div>
        </div>
      </div>

      <!-- Grupo Econômico & Risco Cruzado QSA -->
      <div
        v-if="committee.economic_group?.linked_count > 0"
        class="p-3 rounded-lg bg-surface-amber-1 border border-outline-amber-2 space-y-1.5 text-p-sm"
      >
        <div class="font-semibold text-ink-amber-4">
          🔗 {{ __('Grupo Econômico Detectado ({0} empresas ligadas pelos mesmos sócios no QSA)', [committee.economic_group.linked_count]) }}
        </div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="rel in committee.economic_group.related_organizations"
            :key="rel.organization"
            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-white border border-outline-gray-2 text-xs text-ink-gray-8"
          >
            <strong>{{ rel.organization_name }}</strong>
            <span v-if="rel.cnpj" class="text-ink-gray-5">({{ rel.cnpj }})</span>
            <span class="text-ink-amber-4">· {{ (rel.shared_partners || []).join(', ') }}</span>
          </span>
        </div>
      </div>

      <!-- Votos Registrados na Mesa de Comitê -->
      <div v-if="committee.votes?.length" class="space-y-1.5">
        <div class="text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
          {{ __('Trilha de Votos do Comitê ({0}/{1} aprovações)', [committee.approve_count || 0, committee.required_quorum || 1]) }}
        </div>
        <div class="divide-y divide-outline-gray-1 border border-outline-gray-2 rounded-lg">
          <div
            v-for="(v, i) in committee.votes"
            :key="i"
            class="px-3 py-2 flex flex-wrap items-center justify-between gap-2 text-xs"
          >
            <div>
              <strong class="text-ink-gray-9">{{ v.full_name || v.user }}</strong>
              <span class="text-ink-gray-5 ml-2">{{ v.voted_on }}</span>
              <span v-if="v.notes" class="block text-ink-gray-7 mt-0.5">💬 {{ v.notes }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-medium text-ink-gray-8">{{ formatBRL(v.voted_limit || 0) }}</span>
              <Badge
                :theme="v.vote === 'approve' ? 'green' : v.vote === 'reject' ? 'red' : 'amber'"
                variant="subtle"
                size="sm"
              >
                {{ v.vote === 'approve' ? __('Aprovou') : v.vote === 'reject' ? __('Reprovou') : __('Com Condicionantes') }}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- Formulário de Alçada e Votação -->
      <div
        v-if="showCommitteeForm"
        class="pt-3 border-t border-outline-gray-2 space-y-4"
      >
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <FormControl
            v-model="committeeDraft.proposed_limit"
            type="number"
            :label="__('Limite Proposto (R$)')"
          />
          <FormControl
            v-model="committeeDraft.proposed_concentration"
            type="number"
            :label="__('Máx. por Sacado (R$)')"
          />
          <FormControl
            v-model="committeeDraft.required_quorum"
            type="number"
            :label="__('Quórum (Nº de Aprovadores)')"
          />
          <FormControl
            v-model="committeeDraft.validity_days"
            type="number"
            :label="__('Prazo de Vigência (dias)')"
          />
        </div>
        <FormControl
          v-model="committeeDraft.conditions_notes"
          type="textarea"
          :rows="2"
          :label="__('Condicionantes / Garantias exigidas (Aval, Duplicata Performada, Alienação, etc.)')"
        />
        <div class="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            :loading="savingCommittee"
            @click="saveCommitteeProposal"
          >
            {{ __('Salvar Proposta de Alçada') }}
          </Button>
          <Button
            variant="solid"
            theme="green"
            size="sm"
            :loading="savingCommittee"
            @click="castVote('approve')"
          >
            ✓ {{ __('Votar: Aprovar Limite') }}
          </Button>
          <Button
            variant="subtle"
            size="sm"
            :loading="savingCommittee"
            @click="castVote('approve_with_conditions')"
          >
            ⚠ {{ __('Votar: Aprovar com Condicionantes') }}
          </Button>
          <Button
            variant="outline"
            theme="red"
            size="sm"
            :loading="savingCommittee"
            @click="castVote('reject')"
          >
            ✕ {{ __('Votar: Reprovar') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- Modal de Recusa de Documento com Motivo e Chips Rápidos -->
    <Dialog
      v-model:open="showRejectModal"
      :title="__('Recusar Documento · {0}', [rejectingItem?.label || ''])"
      size="lg"
    >
      <template #default>
        <div class="space-y-4 pt-1">
          <p class="text-xs text-[#5E6068]">
            {{
              __(
                'O documento será marcado como recusado, o motivo será registrado na timeline e exibido com destaque na Pasta Digital do cedente para substituição imediata.',
              )
            }}
          </p>

          <!-- Sugestão da IA (se houver) -->
          <div
            v-if="rejectingItem?.extracted_data?.suggested_reason"
            class="p-2.5 rounded-lg bg-[#FFF4D6] border border-[#FEEA9F] text-xs text-[#8A5A00] flex items-center justify-between gap-2"
          >
            <div class="flex items-center gap-1.5 min-w-0 flex-1">
              <span class="font-bold shrink-0">✨ {{ __('Sugestão da IA') }}:</span>
              <span class="truncate">{{ rejectingItem.extracted_data.suggested_reason }}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              class="shrink-0 bg-white text-[#8A5A00] border-[#FEEA9F] hover:bg-[#FEF3D6] text-xs py-0.5 h-6"
              @click="applyQuickReason(rejectingItem.extracted_data.suggested_reason)"
            >
              {{ __('Usar motivo') }}
            </Button>
          </div>

          <!-- Chips de Motivos Rápidos -->
          <div class="space-y-1.5">
            <label class="text-xs font-semibold text-[#1E1F23]">
              {{ __('Motivos rápidos (clique para preencher):') }}
            </label>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="r in quickRejectionReasons"
                :key="r"
                type="button"
                class="px-2.5 py-1 rounded-full text-xs font-medium border border-[#DCDDE2] bg-[#F5F5F7] text-[#2A2B30] hover:bg-[#E6E7EB] hover:border-[#8A8C94] transition-colors"
                @click="applyQuickReason(r)"
              >
                + {{ r }}
              </button>
            </div>
          </div>

          <!-- Campo de Motivo Livre -->
          <div>
            <label class="block text-xs font-semibold text-[#1E1F23] mb-1">
              {{ __('Motivo da recusa informado ao cliente:') }}
            </label>
            <textarea
              v-model="rejectReasonDraft"
              rows="3"
              class="w-full rounded-lg border border-[#DCDDE2] bg-white p-2.5 text-xs text-[#1E1F23] focus:border-[#0088FF] focus:outline-none"
              :placeholder="
                __('Ex: O contrato social enviado não possui o carimbo da Junta Comercial. Favor anexar a versão autenticada.')
              "
            />
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            size="sm"
            @click="showRejectModal = false"
          >
            {{ __('Cancelar') }}
          </Button>
          <Button
            variant="solid"
            theme="red"
            size="sm"
            :loading="submittingReject"
            :disabled="!rejectReasonDraft.trim()"
            @click="confirmReject"
          >
            {{ __('Confirmar Recusa e Notificar') }}
          </Button>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  Dialog,
  FileUploader,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  organizationId: { type: String, required: true },
  dealId: { type: String, default: '' },
})

const targetDoctype = computed(() =>
  props.dealId ? 'CRM Deal' : 'CRM Organization',
)
const targetDocname = computed(() => props.dealId || props.organizationId)

const onboarding = createResource({
  url: 'cred_hub.credit_check.api.get_credit_onboarding',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
})

const checklist = computed(() => onboarding.data?.checklist || [])
const summary = computed(() => onboarding.data?.summary || null)
const portal = computed(
  () => onboarding.data?.portal || { active: false, url: '', path: '' },
)
const portalFullUrl = computed(() => {
  if (!portal.value?.active) return ''
  if (portal.value.path && typeof window !== 'undefined') {
    return `${window.location.origin}${portal.value.path}`
  }
  return portal.value.url || ''
})
const visit = computed(
  () =>
    onboarding.data?.visit || {
      status: 'not_done',
      visit_date: '',
      visitor_name: '',
      visit_type: 'presencial',
      property_type: 'alugado',
      operational_status: 'otimo',
      inventory_level: 'normal',
      employees_observed: '',
      recommendation: 'favoravel',
      notes: '',
      photos: [],
    },
)

const generatingLink = ref(false)
const showAddCustom = ref(false)
const customDocLabel = ref('')
const customDocCategory = ref('Lastro')
const addingCustom = ref(false)

async function generateLink(regenerate = false) {
  generatingLink.value = true
  try {
    const res = await call('cred_hub.credit_check.api.generate_portal_link', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      regenerate: regenerate ? 1 : 0,
    })
    onboarding.data = res
    toast.success(__('Link seguro da Pasta Digital gerado!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível gerar o link.'))
  } finally {
    generatingLink.value = false
  }
}

async function revokeLink() {
  generatingLink.value = true
  try {
    const res = await call('cred_hub.credit_check.api.revoke_portal_link', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
    })
    onboarding.data = res
    toast.success(__('Link externo desativado.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível desativar o link.'))
  } finally {
    generatingLink.value = false
  }
}

async function copyPortalLink() {
  const url = portalFullUrl.value
  if (!url) return
  try {
    await navigator.clipboard.writeText(url)
    toast.success(__('Link copiado para a área de transferência!'))
  } catch {
    toast.success(url)
  }
}

async function addCustomItem() {
  if (!customDocLabel.value.trim()) return
  addingCustom.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.add_custom_checklist_item',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        label: customDocLabel.value.trim(),
        category: customDocCategory.value,
        required: 1,
      },
    )
    onboarding.data = res
    customDocLabel.value = ''
    showAddCustom.value = false
    toast.success(__('Documento específico adicionado à pasta!'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível adicionar o documento.'),
    )
  } finally {
    addingCustom.value = false
  }
}

async function removeCustomItem(itemKey) {
  try {
    const res = await call(
      'cred_hub.credit_check.api.remove_custom_checklist_item',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        item_key: itemKey,
      },
    )
    onboarding.data = res
    toast.success(__('Documento específico removido.'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível remover o documento.'),
    )
  }
}

const savingKey = ref('')
const analyzingKey = ref('')
const loadingWhatsapp = ref(false)
const editingNoteKey = ref('')
const noteDraft = ref('')

const committee = computed(() => onboarding.data?.committee || null)
const showCommitteeForm = ref(false)
const savingCommittee = ref(false)
const committeeDraft = reactive({
  proposed_limit: 0,
  proposed_concentration: 0,
  required_quorum: 1,
  validity_days: 180,
  conditions_notes: '',
})

watch(
  () => onboarding.data?.committee,
  (c) => {
    if (!c) return
    committeeDraft.proposed_limit =
      c.proposed_limit || c.rating?.suggested_limit || 0
    committeeDraft.proposed_concentration =
      c.proposed_concentration || c.rating?.suggested_max_concentration || 0
    committeeDraft.required_quorum = c.required_quorum || 1
    committeeDraft.validity_days = c.validity_days || 180
    committeeDraft.conditions_notes = c.conditions_notes || ''
  },
  { immediate: true },
)

const showVisitForm = ref(false)
const savingVisit = ref(false)
const visitDraft = reactive({
  status: 'completed',
  visit_date: new Date().toISOString().slice(0, 10),
  visitor_name: '',
  visit_type: 'presencial',
  property_type: 'alugado',
  operational_status: 'otimo',
  inventory_level: 'normal',
  employees_observed: '',
  recommendation: 'favoravel',
  notes: '',
  photos: [],
})

watch(
  () => onboarding.data?.visit,
  (v) => {
    if (!v) return
    visitDraft.status = v.status === 'not_done' ? 'completed' : v.status
    visitDraft.visit_date =
      v.visit_date || new Date().toISOString().slice(0, 10)
    visitDraft.visitor_name = v.visitor_name || ''
    visitDraft.visit_type = v.visit_type || 'presencial'
    visitDraft.property_type = v.property_type || 'alugado'
    visitDraft.operational_status = v.operational_status || 'otimo'
    visitDraft.inventory_level = v.inventory_level || 'normal'
    visitDraft.employees_observed = v.employees_observed || ''
    visitDraft.recommendation = v.recommendation || 'favoravel'
    visitDraft.notes = v.notes || ''
    visitDraft.photos = Array.isArray(v.photos) ? [...v.photos] : []
  },
  { immediate: true },
)

function statusLabel(status) {
  if (status === 'verified') return __('Conferido ✓')
  if (status === 'attached') return __('Anexado')
  if (status === 'rejected') return __('Rejeitado')
  return __('Pendente')
}

function statusTheme(status) {
  if (status === 'verified') return 'green'
  if (status === 'attached') return 'blue'
  if (status === 'rejected') return 'red'
  return 'gray'
}

async function updateItem(itemKey, payload, successMessage) {
  savingKey.value = itemKey
  try {
    const res = await call('cred_hub.credit_check.api.update_checklist_item', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      item_key: itemKey,
      ...payload,
    })
    onboarding.data = res
    if (successMessage) toast.success(successMessage)
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível atualizar o item.'))
  } finally {
    savingKey.value = ''
  }
}

function toggleVerified(item) {
  const nextStatus =
    item.status === 'verified'
      ? item.file_url
        ? 'attached'
        : 'pending'
      : 'verified'
  updateItem(
    item.key,
    { status: nextStatus },
    nextStatus === 'verified'
      ? __('Documento marcado como conferido ✓')
      : __('Conferência desmarcada.'),
  )
}

function markStatus(item, status) {
  updateItem(
    item.key,
    { status },
    status === 'verified'
      ? __('Documento conferido ✓')
      : __('Status do documento atualizado.'),
  )
}

function onFileUploaded(item, file) {
  const fileUrl = file?.file_url || ''
  const fileName = file?.file_name || ''
  if (!fileUrl) return
  updateItem(
    item.key,
    {
      file_url: fileUrl,
      file_name: fileName,
      status: item.status === 'verified' ? 'verified' : 'attached',
    },
    __('Documento anexado na pasta de crédito.'),
  )
}

const showRejectModal = ref(false)
const rejectingItem = ref(null)
const rejectReasonDraft = ref('')
const submittingReject = ref(false)

const quickRejectionReasons = [
  __('Documento ilegível ou cortado'),
  __('Falta assinatura (Junta Comercial / Sócio / Contador)'),
  __('CNPJ ou Razão Social divergente do cadastro'),
  __('Documento incorreto (tipo diferente do solicitado)'),
  __('Documento vencido ou fora do período exigido'),
]

function openRejectModal(item, prefillReason = '') {
  rejectingItem.value = item
  // Se o item já estava com status 'rejected', reaproveita o motivo;
  // se estava em outro status, não puxa notas internas do analista para evitar vazamento acidental.
  const existingRejectionReason = item.status === 'rejected' ? item.notes : ''
  rejectReasonDraft.value = prefillReason || existingRejectionReason || ''
  showRejectModal.value = true
}

function applyQuickReason(reason) {
  if (rejectReasonDraft.value && !rejectReasonDraft.value.includes(reason)) {
    rejectReasonDraft.value = `${rejectReasonDraft.value} · ${reason}`
  } else {
    rejectReasonDraft.value = reason
  }
}

async function confirmReject() {
  if (!rejectingItem.value || !rejectReasonDraft.value.trim()) return
  submittingReject.value = true
  try {
    await updateItem(
      rejectingItem.value.key,
      {
        status: 'rejected',
        notes: rejectReasonDraft.value.trim(),
      },
      __('Documento recusado. O cedente foi notificado e pode reenviar pelo link.'),
    )
    showRejectModal.value = false
    rejectingItem.value = null
    rejectReasonDraft.value = ''
  } finally {
    submittingReject.value = false
  }
}

function openNoteEditor(item) {
  if (editingNoteKey.value === item.key) {
    editingNoteKey.value = ''
    return
  }
  noteDraft.value = item.notes || ''
  editingNoteKey.value = item.key
}

async function saveNoteAndStatus(item, nextStatus) {
  await updateItem(
    item.key,
    {
      status: nextStatus,
      notes: noteDraft.value,
    },
    nextStatus === 'rejected'
      ? __('Documento marcado para reenvio.')
      : __('Observação salva.'),
  )
  editingNoteKey.value = ''
}

function onValidUntilChange(item, newDate) {
  updateItem(
    item.key,
    { valid_until: newDate || '' },
    newDate
      ? __('Data de vencimento do documento salva ({0}).', [newDate])
      : __('Data de vencimento removida.'),
  )
}

async function analyzeDocument(item) {
  analyzingKey.value = item.key
  try {
    const res = await call(
      'cred_hub.credit_check.api.analyze_checklist_document',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        item_key: item.key,
      },
    )
    onboarding.data = res
    toast.success(__('Leitura inteligente concluída!'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível analisar o documento.'),
    )
  } finally {
    analyzingKey.value = ''
  }
}

async function sendWhatsappReminder() {
  loadingWhatsapp.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.get_whatsapp_onboarding_reminder',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
      },
    )
    if (res?.whatsapp_web_url) {
      window.open(res.whatsapp_web_url, '_blank', 'noopener')
      toast.success(__('Cobrança de documentos aberta no WhatsApp!'))
    } else if (res?.message) {
      await navigator.clipboard.writeText(res.message)
      toast.success(
        __(
          'Mensagem de cobrança copiada para a área de transferência (cadastre o celular do contato para abrir direto no WhatsApp).',
        ),
      )
    }
  } catch (err) {
    toast.error(
      err?.messages?.[0] ||
        __('Não foi possível gerar o lembrete de WhatsApp.'),
    )
  } finally {
    loadingWhatsapp.value = false
  }
}

function formatBRL(val) {
  const num = Number(val || 0)
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  })
}

function ratingTheme(r) {
  if (r === 'AA' || r === 'A') return 'green'
  if (r === 'B') return 'blue'
  if (r === 'C') return 'amber'
  return 'red'
}

function committeeStatusLabel(st) {
  if (st === 'approved') return __('Alçada Aprovada ✓')
  if (st === 'approved_with_conditions')
    return __('Aprovado c/ Condicionantes')
  if (st === 'rejected') return __('Alçada Reprovada')
  if (st === 'in_voting') return __('Em Votação no Comitê')
  return __('Aguardando Deliberação')
}

function committeeStatusTheme(st) {
  if (st === 'approved') return 'green'
  if (st === 'approved_with_conditions') return 'amber'
  if (st === 'rejected') return 'red'
  if (st === 'in_voting') return 'blue'
  return 'gray'
}

async function saveCommitteeProposal() {
  savingCommittee.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.save_committee_proposal',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        proposed_limit: Number(committeeDraft.proposed_limit || 0),
        proposed_concentration: Number(
          committeeDraft.proposed_concentration || 0,
        ),
        required_quorum: Number(committeeDraft.required_quorum || 1),
        validity_days: Number(committeeDraft.validity_days || 180),
        conditions_notes: committeeDraft.conditions_notes || '',
      },
    )
    onboarding.data = res
    toast.success(__('Proposta de alçada salva na Mesa de Comitê!'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível salvar a proposta.'),
    )
  } finally {
    savingCommittee.value = false
  }
}

async function castVote(voteType) {
  savingCommittee.value = true
  try {
    await call('cred_hub.credit_check.api.save_committee_proposal', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      proposed_limit: Number(committeeDraft.proposed_limit || 0),
      proposed_concentration: Number(
        committeeDraft.proposed_concentration || 0,
      ),
      required_quorum: Number(committeeDraft.required_quorum || 1),
      validity_days: Number(committeeDraft.validity_days || 180),
      conditions_notes: committeeDraft.conditions_notes || '',
    })
    const res = await call('cred_hub.credit_check.api.cast_committee_vote', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      vote: voteType,
      voted_limit: Number(committeeDraft.proposed_limit || 0),
      notes: committeeDraft.conditions_notes || '',
    })
    onboarding.data = res
    toast.success(__('Voto registrado na Mesa de Comitê!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível registrar o voto.'))
  } finally {
    savingCommittee.value = false
  }
}

const visitStatusLabel = computed(() => {
  if (visit.value.status === 'completed') return __('Visita Realizada')
  if (visit.value.status === 'scheduled') return __('Visita Agendada')
  return __('Visita não registrada')
})

const visitStatusTheme = computed(() => {
  if (visit.value.status === 'completed') return 'green'
  if (visit.value.status === 'scheduled') return 'blue'
  return 'gray'
})

const visitRecLabel = computed(() => {
  if (visit.value.recommendation === 'favoravel')
    return __('Parecer: Favorável')
  if (visit.value.recommendation === 'desfavoravel')
    return __('Parecer: Desfavorável')
  return __('Parecer: Com ressalvas')
})

const visitRecTheme = computed(() => {
  if (visit.value.recommendation === 'favoravel') return 'green'
  if (visit.value.recommendation === 'desfavoravel') return 'red'
  return 'amber'
})

function visitTypeLabel(v) {
  if (v === 'video') return __('Vídeo / Remota')
  if (v === 'terceirizada') return __('Terceirizada')
  return __('Presencial (in loco)')
}

function propertyTypeLabel(v) {
  if (v === 'proprio') return __('Imóvel Próprio')
  if (v === 'cedido') return __('Cedido / Condomínio')
  return __('Imóvel Alugado')
}

function operationalLabel(v) {
  if (v === 'otimo') return __('Plena atividade / Boa estrutura')
  if (v === 'precario') return __('Estrutura precária / Baixa movimentação')
  if (v === 'incompativel')
    return __('Incompatível com faturamento declarado')
  return __('Operação regular')
}

function inventoryLabel(v) {
  if (v === 'alto') return __('Estoque / Produção alta')
  if (v === 'baixo') return __('Estoque baixo')
  if (v === 'servicos') return __('Serviços / Não aplicável')
  return __('Normal / Compatível')
}

function onVisitPhotoUploaded(file) {
  if (!file?.file_url) return
  visitDraft.photos.push({
    file_url: file.file_url,
    file_name: file.file_name || __('Foto da visita'),
    uploaded_on: new Date().toISOString().slice(0, 10),
  })
  toast.success(__('Evidência anexada ao relatório de visita.'))
}

function removeVisitPhoto(index) {
  visitDraft.photos.splice(index, 1)
}

async function saveVisit() {
  savingVisit.value = true
  try {
    const res = await call('cred_hub.credit_check.api.save_visit_report', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      visit_data: JSON.stringify(visitDraft),
    })
    onboarding.data = res
    showVisitForm.value = false
    toast.success(__('Relatório de visita salvo com sucesso!'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível salvar o relatório de visita.'),
    )
  } finally {
    savingVisit.value = false
  }
}
</script>
