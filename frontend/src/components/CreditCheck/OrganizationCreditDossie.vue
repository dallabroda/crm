<template>
  <!-- Figma "Card · Análise de crédito · preenchida" (2164:12977): one white
       card per section (grey border, radius 8, padding 20), 16px between them -->
  <div class="flex max-w-[984px] flex-col gap-4 p-5">
    <!-- 1. Esteira progressiva (3 níveis) + valor pretendido -->
    <section :class="cardClass" class="gap-[18px]">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-0.5">
          <div class="flex items-center gap-4">
            <h2 :class="titleClass" class="min-w-0 flex-1">
              {{ __('Esteira Progressiva de Análise de Crédito (3 Níveis)') }}
            </h2>
            <router-link
              v-if="canOpenSettings"
              :to="creditSettingsRoute"
              class="flex h-8 shrink-0 items-center gap-1.5 rounded-[var(--ct-radius-sm)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] px-4 text-[14px] font-medium leading-5 text-[color:var(--ct-text-primary)] transition-colors hover:bg-[var(--ct-bg-soft)]"
            >
              <span class="lucide-settings size-4" aria-hidden="true" />
              {{ __('Configurações') }}
            </router-link>
          </div>
          <p
            class="text-[12px] leading-4 text-[color:var(--ct-text-secondary)]"
          >
            {{
              __(
                'Avance conforme o ticket da operação para proteger o custo de API da sua conta nos bureaus.',
              )
            }}
          </p>
        </div>

        <!-- Figma "Campo" (Valor pretendido): label 14 Medium, box 48px -->
        <label class="flex w-[290px] max-w-full flex-col gap-1.5">
          <span :class="fieldLabelClass">{{
            __('Valor pretendido (R$)')
          }}</span>
          <input
            :value="amountDisplay"
            type="text"
            inputmode="decimal"
            :placeholder="__('Ex.: 50.000,00')"
            :class="fieldBoxClass"
            @focus="onAmountFocus"
            @input="amountDraft = $event.target.value"
            @blur="onAmountBlur"
            @keydown.enter="$event.target.blur()"
          />
        </label>
      </div>

      <!-- 3 níveis lado a lado. Níveis 2 e 3 escolhem o pacote do dossiê. -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div :class="levelCardClass(false)">
          <div class="flex flex-col gap-3">
            <span :class="pillClass(levelOneStatus.tone)" class="self-start">
              <span :class="dotClass(levelOneStatus.tone)" />
              {{ levelOneStatus.label }}
            </span>
            <h3 :class="levelTitleClass">{{ __('Nível 1 · Triagem') }}</h3>
          </div>
          <p :class="levelTextClass">
            {{
              __(
                'Receita Federal/QSA, CGU CEIS/CNEP (grátis), Sintegra UF (R$ 0,36) e FGTS (R$ 0,36). Elimina empresas inaptas logo no início.',
              )
            }}
          </p>
        </div>

        <button
          type="button"
          :class="levelCardClass(selectedTierMode === 'tier_2')"
          :aria-pressed="selectedTierMode === 'tier_2'"
          @click="toggleTierMode('tier_2')"
        >
          <h3 :class="levelTitleClass">{{ __('Nível 2 · Dossiê base') }}</h3>
          <p :class="levelTextClass">
            {{
              __(
                'Dossiê QUOD Completo (score, protestos, ações e cheques) + SCR Bacen. Indicado para tickets pequenos e médios.',
              )
            }}
          </p>
          <span :class="levelCostClass">{{ __('R$ 10,89 por empresa') }}</span>
        </button>

        <button
          type="button"
          :class="levelCardClass(selectedTierMode.startsWith('tier_3'))"
          :aria-pressed="selectedTierMode.startsWith('tier_3')"
          @click="toggleTierMode('tier_3_boavista')"
        >
          <h3 :class="levelTitleClass">
            {{ __('Nível 3 · Profundo (ticket alto)') }}
          </h3>
          <p :class="levelTextClass">
            {{
              __(
                'Boa Vista Positivo PJ (ou Serasa) + SCR Bacen + processos com penhoras + sócios PF. Dá para pular direto do Nível 1 para cá em operações maiores.',
              )
            }}
          </p>
          <span :class="levelCostClass">
            {{ __('Positivo + penhoras + sócios') }}
          </span>
          <!-- Boa Vista or Serasa, only once level 3 is chosen -->
          <span
            v-if="selectedTierMode.startsWith('tier_3')"
            class="flex flex-wrap gap-x-3 gap-y-1 whitespace-nowrap text-[12px] font-medium leading-4"
          >
            <span
              v-for="opt in tierThreeOptions"
              :key="opt.value"
              role="button"
              tabindex="0"
              :class="
                selectedTierMode === opt.value
                  ? 'text-[color:var(--ct-text-accent)] underline'
                  : 'text-[color:var(--ct-text-secondary)] hover:text-[color:var(--ct-text-primary)]'
              "
              @click.stop="selectTierMode(opt.value)"
              @keydown.enter.stop="selectTierMode(opt.value)"
            >
              {{ opt.label }}
            </span>
          </span>
        </button>
      </div>
    </section>

    <!-- 2. Nível 1 · Triagem cadastral, fiscal e compliance -->
    <section :class="cardClass" class="gap-3">
      <div class="flex flex-col gap-1">
        <div class="flex flex-wrap items-center gap-2">
          <h2 :class="titleClass">
            {{ __('Nível 1 · Triagem cadastral, fiscal e compliance') }}
          </h2>
          <span v-if="org.data?.credit_report" :class="pillClass(verdictTone)">
            <span :class="dotClass(verdictTone)" />
            {{ verdictLabel }}
          </span>
        </div>
        <p v-if="org.data?.cnpj" :class="bodySecondaryClass">
          {{ __('CNPJ') }} {{ org.data.cnpj }}
        </p>
        <p :class="bodySecondaryClass">
          {{
            __(
              'Checagem imediata de Situação Cadastral/QSA, Sanções Públicas CEIS/CNEP (CGU · Grátis), Sintegra/CCC por UF, Regularidade FGTS e Dívida Ativa PGFN antes de consultar bureaus de crédito.',
            )
          }}
        </p>
      </div>

      <!-- Figma "Aviso (toast)" Informação with the white button on the right -->
      <div v-if="isReportError" :class="alertClass('error')">
        <span class="lucide-circle-alert size-5 shrink-0" aria-hidden="true" />
        <p class="min-w-0 flex-1">
          {{ __('Falha na checagem da triagem inicial.') }}
          {{
            report.data?.verdict_summary ||
            __(
              'Ocorreu uma falha na consulta aos serviços externos. Nenhum parecer foi emitido.',
            )
          }}
        </p>
        <button
          type="button"
          :class="alertButtonClass"
          :disabled="checking"
          @click="askRunCheck(true)"
        >
          {{ __('Atualizar triagem') }}
        </button>
      </div>
      <div v-else-if="org.data?.credit_report" :class="alertClass('info')">
        <span class="lucide-info size-5 shrink-0" aria-hidden="true" />
        <p class="min-w-0 flex-1">
          <template v-if="report.data?.checked_on">
            {{
              __(
                'Triagem feita em {0}. Nova consulta liberada a partir de {1}',
                [report.data.checked_on, report.data.valid_until || '—'],
              )
            }}
            <br />
            {{
              __(
                '(prazo de {0} dias, alterável em Configurações › Crédito e cobrança).',
                [pkg.data?.reuse_days ?? 30],
              )
            }}
          </template>
          <template v-else>{{ __('Triagem em andamento…') }}</template>
        </p>
        <button
          type="button"
          :class="alertButtonClass"
          :disabled="checking"
          @click="askRunCheck(true)"
        >
          {{ __('Atualizar triagem') }}
        </button>
      </div>
      <div v-else :class="alertClass('info')">
        <span class="lucide-info size-5 shrink-0" aria-hidden="true" />
        <p class="min-w-0 flex-1">
          {{
            __(
              'Nenhuma triagem jurídica/fiscal foi executada para esta organização ainda.',
            )
          }}
        </p>
        <button
          type="button"
          :class="alertButtonClass"
          :disabled="checking"
          @click="askRunCheck(false)"
        >
          {{ __('Executar triagem') }}
        </button>
      </div>

      <p
        v-if="isReportSuccess && showVerdictSummary"
        :class="bodySecondaryClass"
      >
        {{ report.data.verdict_summary }}
      </p>

      <div v-if="report.data && !isReportError" class="flex flex-col">
        <div v-for="row in triageRows" :key="row.label" :class="rowClass">
          <span :class="rowLabelClass">{{ row.label }}</span>
          <span :class="rowValueClass(row.tone)">{{ row.value }}</span>
        </div>
      </div>
    </section>

    <!-- 3. Resumo executivo unificado dos bureaus -->
    <section v-if="hasHighlights" :class="cardClass" class="gap-4">
      <div class="flex flex-col gap-0.5">
        <h2 :class="titleClass">
          {{ __('Resumo Executivo Unificado dos Bureaus') }}
        </h2>
        <p class="text-[12px] leading-4 text-[color:var(--ct-text-secondary)]">
          {{
            __(
              'Indicadores consolidados automaticamente a partir das consultas realizadas (QUOD, Boa Vista, Serasa, SCR Bacen e Processos).',
            )
          }}
        </p>
      </div>

      <div
        v-for="(alert, idx) in highlights.data?.fraud_alerts || []"
        :key="'alert-' + idx"
        :class="alertClass(alert.severity === 'critical' ? 'error' : 'warning')"
      >
        <span
          class="lucide-triangle-alert size-5 shrink-0"
          aria-hidden="true"
        />
        <p class="min-w-0 flex-1">
          {{ alert.title }}
          <span class="font-normal">· {{ alert.detail }}</span>
        </p>
      </div>

      <div class="flex flex-col gap-2">
        <template v-for="group in highlightGroups" :key="group.key">
          <div class="flex flex-col" :class="group.rows.length ? '' : 'gap-1'">
            <h3 :class="groupTitleClass">{{ group.title }}</h3>
            <div v-for="row in group.rows" :key="row.label" :class="rowClass">
              <span :class="rowLabelClass">{{ row.label }}</span>
              <span :class="rowValueClass(row.tone)">{{ row.value }}</span>
            </div>
            <p
              v-if="!group.rows.length"
              class="text-[12px] leading-4 text-[color:var(--ct-text-tertiary)]"
            >
              {{ group.empty }}
            </p>
          </div>
          <!-- Figma "Divisor" Linha -->
          <div v-if="group.divider" class="flex h-5 items-center">
            <div class="h-px flex-1 bg-[var(--ct-border)]" />
          </div>
        </template>
      </div>
    </section>

    <!-- 4. Quadro societário (seleção de sócios para consulta PF) -->
    <section
      v-if="partners.data && partners.data.length"
      :class="cardClass"
      class="gap-1.5"
    >
      <div class="flex items-center gap-2">
        <h2 :class="titleClass" class="min-w-0 flex-1">
          {{ __('Quadro Societário (Seleção de Sócios para Consulta PF)') }}
        </h2>
        <button
          type="button"
          class="flex size-8 shrink-0 items-center justify-center rounded-[var(--ct-radius-sm)] text-[color:var(--ct-text-primary)] hover:bg-[var(--ct-bg-soft)]"
          :aria-expanded="partnersOpen"
          :aria-label="partnersOpen ? __('Recolher') : __('Expandir')"
          @click="partnersOpen = !partnersOpen"
        >
          <span
            :class="partnersOpen ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            class="size-4"
            aria-hidden="true"
          />
        </button>
      </div>
      <template v-if="partnersOpen">
        <p
          class="max-w-[735px] text-[12px] leading-5 text-[color:var(--ct-text-secondary)]"
        >
          {{
            __(
              'Por padrão, pré-selecionamos apenas o(s) Sócio(s)-Administrador(es) para evitar cobrança multiplicada em sócios minoritários. Marque ou desmarque quem deseja consultar no Dossiê ou em consultas avulsas.',
            )
          }}
        </p>

        <div
          v-for="partner in partners.data"
          :key="partner.contact"
          class="flex items-center gap-3 py-3"
        >
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <!-- Figma "Caixa de seleção": 20px, radius 6, blue when checked -->
            <label
              class="flex items-start gap-2"
              :class="partner.has_cpf ? 'cursor-pointer' : 'cursor-not-allowed'"
            >
              <input
                type="checkbox"
                class="peer sr-only"
                :checked="selected.includes(partner.contact)"
                :disabled="!partner.has_cpf"
                @change="togglePartner(partner.contact)"
              />
              <span
                class="flex size-5 shrink-0 items-center justify-center rounded-[var(--ct-radius-sm)] border peer-focus-visible:ring-2 peer-focus-visible:ring-[var(--ct-accent-soft-hover)]"
                :class="
                  selected.includes(partner.contact)
                    ? 'border-[var(--ct-accent)] bg-[var(--ct-accent)] text-white'
                    : 'border-[var(--ct-border)] bg-[var(--ct-bg-page)]'
                "
                aria-hidden="true"
              >
                <span
                  v-if="selected.includes(partner.contact)"
                  class="lucide-check size-3.5"
                />
              </span>
              <span
                class="min-w-0 truncate text-[14px] leading-5 text-[color:var(--ct-text-primary)]"
              >
                {{ partner.name }}
              </span>
            </label>
            <span
              class="pl-7 text-[12px] text-[color:var(--ct-text-secondary)]"
            >
              {{ partnerRole(partner) }}
            </span>
          </div>
          <span
            v-if="partner.has_cpf"
            class="shrink-0 text-[14px] leading-5 text-[color:var(--ct-text-primary)]"
          >
            {{ partner.cpf }}
          </span>
          <template v-else>
            <input
              v-model="cpfDraft[partner.contact]"
              type="text"
              inputmode="numeric"
              :placeholder="__('CPF completo')"
              :aria-label="__('CPF completo de {0}', [partner.name])"
              :class="fieldBoxClass"
              class="w-[200px] shrink-0"
            />
            <Button
              variant="outline"
              :loading="savingCpf === partner.contact"
              :disabled="!cpfDraft[partner.contact]"
              @click="saveCpf(partner)"
            >
              {{ __('Salvar CPF') }}
            </Button>
          </template>
        </div>

        <!-- Bureaus PF para os sócios marcados (consultas pagas por sócio) -->
        <div
          v-if="partnerBureaus.length"
          class="flex flex-wrap items-end gap-4"
        >
          <div class="flex w-[485px] max-w-full flex-col gap-1.5">
            <span :class="fieldLabelClass">
              {{ __('Bureaus para os sócios marcados') }}
            </span>
            <Popover
              side="bottom"
              align="start"
              :offset="4"
              bare
              match-trigger-width
            >
              <template #trigger="{ open: isOpen }">
                <button
                  type="button"
                  :class="fieldBoxClass"
                  class="flex w-full items-center gap-2 text-left"
                >
                  <span
                    class="min-w-0 flex-1 truncate"
                    :class="
                      chosenPartnerBureaus.length
                        ? ''
                        : 'text-[color:var(--ct-text-tertiary)]'
                    "
                  >
                    {{
                      chosenPartnerBureaus.length
                        ? chosenPartnerBureaus.map((b) => b.label).join(', ')
                        : __('Selecione os bureaus')
                    }}
                  </span>
                  <span
                    :class="
                      isOpen ? 'lucide-chevron-up' : 'lucide-chevron-down'
                    "
                    class="size-5 shrink-0"
                    aria-hidden="true"
                  />
                </button>
              </template>
              <template #default>
                <div
                  class="rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] p-1 shadow-lg"
                >
                  <label
                    v-for="bureau in partnerBureaus"
                    :key="bureau.key"
                    class="flex items-center gap-2 rounded-[var(--ct-radius-sm)] px-2.5 py-2 text-[14px] leading-5"
                    :class="
                      bureau.configured
                        ? 'cursor-pointer hover:bg-[var(--ct-bg-soft)]'
                        : 'cursor-not-allowed opacity-50'
                    "
                  >
                    <input
                      type="checkbox"
                      class="size-4 accent-[var(--ct-accent)]"
                      :checked="partnerBureauKeys.includes(bureau.key)"
                      :disabled="!bureau.configured"
                      @change="togglePartnerBureau(bureau.key)"
                    />
                    <span class="min-w-0 flex-1 truncate">{{
                      bureau.label
                    }}</span>
                    <span
                      class="shrink-0 text-[12px] text-[color:var(--ct-text-tertiary)]"
                    >
                      {{
                        bureau.configured
                          ? bureau.price_reference
                            ? formatMoney(bureau.price_reference)
                            : bureau.provider
                          : __('sem credencial')
                      }}
                    </span>
                  </label>
                </div>
              </template>
            </Popover>
          </div>
          <div class="pb-2">
            <Button
              variant="outline"
              class="w-[130px]"
              :loading="requesting.endsWith(':partners')"
              :disabled="!canRunPartnerBureaus"
              @click="askPartnerBureaus"
            >
              {{ __('Gerar bureaus') }}
            </Button>
          </div>
        </div>
      </template>
    </section>

    <!-- 5. Gerar dossiê de crédito (nível 2 ou 3) + documentos gerados -->
    <section v-if="pkg.data" :class="cardClass" class="gap-3">
      <div class="flex items-center gap-2">
        <h2 :class="titleClass" class="min-w-0 flex-1">
          {{
            __('Gerar Dossiê de Crédito (Nível 2 Médio ou Nível 3 Profundo)')
          }}
        </h2>
        <span v-if="pkgRunning" :class="pillClass('info')">
          <span :class="dotClass('info')" />
          {{ __('Gerando…') }}
        </span>
      </div>

      <div class="flex flex-col gap-1.5">
        <h3
          class="text-[12px] font-semibold uppercase leading-4 tracking-[0.6px] text-[color:var(--ct-text-secondary)]"
        >
          {{ __('Consultas incluídas nesta execução') }}
        </h3>
        <p
          v-if="!pkg.data.items?.length"
          class="text-[14px] leading-5 text-[color:var(--ct-text-tertiary)]"
        >
          {{
            __(
              'Nenhuma consulta sob demanda configurada para o nível selecionado.',
            )
          }}
        </p>
        <div
          v-for="entry in pkg.data.items"
          :key="entry.item + (entry.contact || '')"
          class="flex items-start gap-2 text-[14px] leading-5"
        >
          <span
            class="shrink-0 font-bold"
            :class="
              entry.state === 'reused'
                ? 'text-[color:var(--ct-success)]'
                : entry.state === 'unavailable'
                  ? 'text-[color:var(--ct-error)]'
                  : 'text-[color:var(--ct-accent)]'
            "
            aria-hidden="true"
            >{{ entry.state === 'reused' ? '✓' : '•' }}</span
          >
          <div class="min-w-0 flex-1">
            <span class="font-medium text-[#2a2b30]"
              >{{ entry.label }} · {{ entry.subject_name }}</span
            >
            <span class="text-[color:var(--ct-text-tertiary)]">
              — {{ packageEntryText(entry) }}</span
            >
            <div v-if="entry.last_error" class="text-[color:var(--ct-error)]">
              {{ __('Última tentativa falhou: {0}', [entry.last_error]) }}
            </div>
          </div>
        </div>
        <p
          v-if="pkg.data.partners_without_cpf.length"
          class="text-[12px] leading-4 text-[color:var(--ct-text-secondary)]"
        >
          {{
            __('Sócios sem CPF completo ficam de fora do pacote: {0}.', [
              pkg.data.partners_without_cpf.join(', '),
            ])
          }}
        </p>
      </div>

      <p class="text-[14px] font-medium leading-5 text-[#2a2b30]">
        {{ packageSummary }}
      </p>
      <p
        v-if="pkg.data.unavailable.length"
        class="text-[14px] leading-5 text-[color:var(--ct-error)]"
      >
        {{
          __(
            'Um administrador precisa habilitar e configurar o token destes bureaus ou retirá-los do pacote em Configurações > Bureaus e Crédito.',
          )
        }}
      </p>
      <p
        v-if="opinionNote"
        class="text-[14px] font-medium leading-5 text-[color:var(--ct-warning)]"
      >
        {{ opinionNote }}
      </p>
      <div>
        <Button
          variant="solid"
          iconLeft="lucide-file-text"
          :loading="startingPackage"
          :disabled="!canGeneratePackage"
          @click="askPackage"
        >
          {{ __('Gerar Dossiê Completo (PDF)') }}
        </Button>
      </div>

      <template v-if="groupedDossiers.length || opinionDocs.length">
        <h3
          class="text-[14px] font-medium leading-4 text-[color:var(--ct-text-secondary)]"
        >
          {{ __('Documentos gerados') }}
        </h3>
        <div
          v-for="group in groupedDossiers"
          :key="group.key"
          :class="docBoxClass"
        >
          <div class="flex min-w-0 items-center gap-2">
            <a
              v-if="group.pdf"
              :href="group.pdf.file_url"
              target="_blank"
              rel="noopener noreferrer"
              :class="linkClass"
            >
              {{ __('Abrir Dossiê Executivo (PDF)') }}
            </a>
            <span :class="docDateClass"
              >· {{ formatDate(group.creation) }}</span
            >
          </div>
          <a
            v-if="group.json"
            :href="group.json.file_url"
            target="_blank"
            rel="noopener noreferrer"
            :class="linkClass"
          >
            {{ __('JSON bruto (auditoria)') }}
          </a>
        </div>
        <div v-for="item in opinionDocs" :key="item.name" :class="docBoxClass">
          <div class="flex min-w-0 items-center gap-2">
            <a
              v-if="item.pdf_url"
              :href="item.pdf_url"
              target="_blank"
              rel="noopener noreferrer"
              :class="linkClass"
            >
              {{ __('Abrir Parecer de IA (PDF)') }}
            </a>
            <span
              v-else-if="item.status === 'Queued'"
              class="text-[14px] font-medium leading-5 text-[color:var(--ct-text-secondary)]"
            >
              {{ __('Parecer de IA em geração…') }}
            </span>
            <span
              v-else-if="item.status === 'Failed'"
              class="truncate text-[14px] font-medium leading-5 text-[color:var(--ct-error)]"
            >
              {{ __('Falha ao gerar o parecer de IA')
              }}{{ item.error ? `: ${item.error}` : '' }}
            </span>
            <span :class="docDateClass"
              >· {{ formatDate(item.requested_on) }}</span
            >
          </div>
        </div>
      </template>
    </section>

    <!-- 6. Histórico de consultas realizadas -->
    <section
      v-if="results.data && results.data.length"
      :class="cardClass"
      class="gap-3"
    >
      <h2 :class="titleClass">
        {{ __('Histórico de Consultas Realizadas (Relatórios Formatados)') }}
      </h2>
      <div
        v-for="row in results.data"
        :key="row.name"
        class="flex items-center gap-3 border-b border-[var(--ct-border-soft)] py-2"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <span
            class="text-[14px] font-medium leading-5 text-[color:var(--ct-text-primary)]"
          >
            {{ row.bureau_label }}
          </span>
          <span
            class="truncate text-[12px] leading-4 text-[color:var(--ct-text-secondary)]"
          >
            {{ resultMeta(row) }}
          </span>
          <span
            v-if="row.warning_acknowledged"
            class="text-[12px] font-medium leading-4 text-[color:var(--ct-warning)]"
          >
            {{
              __('Consultado com alerta de triagem: {0}', [
                verdictText(row.pre_filter_verdict),
              ])
            }}
          </span>
        </div>
        <Button variant="outline" @click="openResult(row)">
          {{ __('Ver Relatório Formatado') }}
        </Button>
      </div>
    </section>

    <!-- ===================================================================== -->
    <!-- MODAL DO RELATÓRIO DO BUREAU (VISÃO EXECUTIVA FORMATADA + TOGGLE JSON)-->
    <!-- ===================================================================== -->
    <Dialog v-model:open="showResult" :title="resultTitle" :size="'4xl'">
      <template #default>
        <div
          class="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-outline-gray-2"
        >
          <p class="text-p-sm text-ink-gray-6">
            {{
              showRawJson
                ? __(
                    'JSON técnico bruto exatamente como retornado pela API do provedor (para fins de auditoria).',
                  )
                : __(
                    'Relatório formatado com todos os dados oficiais retornados pelo bureau.',
                  )
            }}
          </p>
          <Button
            variant="subtle"
            size="sm"
            @click="showRawJson = !showRawJson"
          >
            {{
              showRawJson
                ? __('Voltar para Visão Formatada')
                : __('Ver JSON Técnico (Auditoria)')
            }}
          </Button>
        </div>

        <div
          v-if="!showRawJson && resultHtml"
          class="overflow-auto max-h-[68vh] pr-1"
          v-html="resultHtml"
        />
        <pre
          v-else
          class="text-p-xs bg-surface-gray-2 rounded p-3 overflow-auto max-h-[65vh] whitespace-pre-wrap"
          >{{ resultText }}</pre>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { Button, Dialog, Popover, createResource, call, toast } from 'frappe-ui'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'
import { settingsRoute } from '@/composables/settingsNavigation'
import { usersStore } from '@/stores/users'

defineEmits(['switch-tab'])

const props = defineProps({
  organizationId: { type: String, required: true },
  // when shown on a card, the queries and comments go to the card (credtech#316)
  dealId: { type: String, default: '' },
})

const checking = ref(false)
const requesting = ref('')
const selected = ref([])
const partnersInitialized = ref(false)
const cpfDraft = reactive({})
const savingCpf = ref('')
const showResult = ref(false)
const showRawJson = ref(false)
const resultTitle = ref('')
const resultText = ref('')
const resultHtml = ref('')
const requestedAmount = ref(0)
const selectedTierMode = ref('default')

const { getUser, isManager } = usersStore()

// ---- Figma 2164:12977 styles (CredTech tokens from theme/credtech.css) ----
const cardClass =
  'flex flex-col rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] p-5'
const titleClass = 'text-[16px] font-semibold leading-6 text-ink-gray-9'
const fieldLabelClass =
  'text-[14px] font-medium leading-5 text-[color:var(--ct-text-secondary)]'
const fieldBoxClass =
  'h-12 rounded-[var(--ct-radius-sm)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] px-3.5 text-[16px] leading-6 text-[color:var(--ct-text-primary)] placeholder:text-[color:var(--ct-text-tertiary)] focus:border-2 focus:border-[var(--ct-border-strong)] focus:px-[13px] focus:outline-none focus:ring-0'
const bodySecondaryClass =
  'text-[14px] leading-5 text-[color:var(--ct-text-secondary)]'
const levelTitleClass =
  'text-[14px] font-semibold text-[color:var(--ct-text-primary)]'
const levelTextClass =
  'text-[14px] leading-5 text-[color:var(--ct-text-secondary)]'
const levelCostClass =
  'text-[12px] font-medium text-[color:var(--ct-text-tertiary)]'
const groupTitleClass =
  'text-[14px] font-medium leading-4 tracking-[0.7px] text-[color:var(--ct-text-primary)]'
const rowClass = 'flex items-start gap-6 py-1.5 text-[14px] leading-[17px]'
const rowLabelClass = 'w-[260px] shrink-0 text-[color:var(--ct-text-secondary)]'
const alertButtonClass =
  'shrink-0 rounded-[var(--ct-radius-sm)] bg-white px-3 py-1 text-[12px] font-medium text-[color:var(--ct-accent)] hover:bg-[var(--ct-bg-soft)] disabled:opacity-40'
const docBoxClass =
  'flex flex-wrap items-center justify-between gap-2 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-[var(--ct-bg-page)] px-4 py-3'
const linkClass =
  'text-[14px] font-medium leading-5 text-[color:var(--ct-text-accent)] underline'
const docDateClass =
  'shrink-0 text-[14px] leading-5 text-[color:var(--ct-text-tertiary)]'

const TONES = {
  success: [
    'bg-[var(--ct-success-soft)] text-[color:var(--ct-success)]',
    'bg-[var(--ct-success)]',
  ],
  warning: [
    'bg-[var(--ct-warning-soft)] text-[color:var(--ct-warning)]',
    'bg-[var(--ct-warning)]',
  ],
  error: [
    'bg-[var(--ct-error-soft)] text-[color:var(--ct-error)]',
    'bg-[var(--ct-error)]',
  ],
  info: [
    'bg-[var(--ct-info-soft)] text-[color:var(--ct-info)]',
    'bg-[var(--ct-info)]',
  ],
  neutral: [
    'bg-[var(--ct-bg-soft)] text-[color:var(--ct-text-secondary)]',
    'bg-[var(--ct-text-tertiary)]',
  ],
}

// Figma "Pílula de status": 12 Medium, 6px dot, pill corners
function pillClass(tone) {
  return `inline-flex shrink-0 items-center gap-1.5 rounded-[var(--ct-radius-pill)] px-2.5 py-0.5 text-[12px] font-medium leading-4 ${(TONES[tone] || TONES.neutral)[0]}`
}
function dotClass(tone) {
  return `size-1.5 rounded-full ${(TONES[tone] || TONES.neutral)[1]}`
}

// Figma "Aviso (toast)": colored strip, 14 Medium, icon 20px
function alertClass(tone) {
  const colors = {
    info: 'bg-[var(--ct-accent-soft)] text-[color:var(--ct-accent)]',
    warning: 'bg-[var(--ct-warning-soft)] text-[color:var(--ct-warning)]',
    error: 'bg-[var(--ct-error-soft)] text-[color:var(--ct-error)]',
  }
  return `flex min-h-11 items-center gap-2.5 rounded-[var(--ct-radius-md)] py-2.5 pl-3.5 pr-2.5 text-[14px] font-medium leading-5 ${colors[tone] || colors.info}`
}

function levelCardClass(active) {
  return `flex flex-col items-start gap-1.5 rounded-[var(--ct-radius-md)] border bg-[var(--ct-bg-page)] p-4 text-left transition-colors ${
    active
      ? 'border-[var(--ct-accent)] ring-1 ring-[var(--ct-accent)]'
      : 'border-[var(--ct-border)]'
  }`
}

function rowValueClass(tone) {
  return `min-w-0 flex-1 truncate ${
    tone === 'error'
      ? 'text-[color:var(--ct-error)]'
      : tone === 'muted'
        ? 'text-[color:var(--ct-text-tertiary)]'
        : 'text-[color:var(--ct-text-primary)]'
  }`
}

const canOpenSettings = computed(() => isManager())
const creditSettingsRoute = settingsRoute('Políticas de Crédito & Compliance')

// "Valor pretendido": shown as 48.730,00, typed freely, parsed on blur
const amountFocused = ref(false)
const amountDraft = ref('')
function formatNumber(value) {
  return Number(value || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}
const amountDisplay = computed(() => {
  if (amountFocused.value) return amountDraft.value
  return requestedAmount.value > 0 ? formatNumber(requestedAmount.value) : ''
})
function onAmountFocus() {
  amountDraft.value =
    requestedAmount.value > 0 ? formatNumber(requestedAmount.value) : ''
  amountFocused.value = true
}
function onAmountBlur() {
  const raw = String(amountDraft.value || '')
    .replace(/[^\d,.-]/g, '')
    .replace(/\./g, '')
    .replace(',', '.')
  const value = Number(raw)
  requestedAmount.value = Number.isFinite(value) && value > 0 ? value : 0
  amountFocused.value = false
}

const tierThreeOptions = [
  { value: 'tier_3_boavista', label: __('Boa Vista Positivo') },
  { value: 'tier_3_serasa', label: __('Serasa Avançado') },
]

const partnersOpen = ref(true)

function partnerRole(partner) {
  return [partner.designation, partner.share != null ? `${partner.share}%` : '']
    .filter(Boolean)
    .join(' · ')
}

const org = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: { name: props.organizationId },
    fieldname: ['credit_verdict', 'credit_report', 'cnpj'],
  },
  auto: true,
  transform: (d) => d?.message || d,
})

watch(
  () => props.organizationId,
  (newId) => {
    if (newId) {
      org.update({
        params: {
          doctype: 'CRM Organization',
          filters: { name: newId },
          fieldname: ['credit_verdict', 'credit_report', 'cnpj'],
        },
      })
      org.fetch()
    }
  },
)

const report = createResource({
  url: 'cred_hub.credit_check.api.get_report_details',
  params: { report_name: org.data?.credit_report },
  auto: false,
})

watch(
  () => org.data?.credit_report,
  (reportName) => {
    if (reportName) {
      report.update({ params: { report_name: reportName } })
      report.fetch()
    }
  },
  { immediate: true },
)

// Consolidated Executive Highlights & Fraud Alerts across all bureau returns
const highlights = createResource({
  url: 'cred_hub.credit_check.api.get_dossier_highlights',
  params: { organization_name: props.organizationId },
  auto: true,
})

const hasHighlights = computed(() => {
  const h = highlights.data
  if (!h) return false
  return Boolean(
    h.scores?.length ||
    h.scr ||
    h.capacity?.presumed_revenue != null ||
    h.capacity?.suggested_limit != null ||
    h.restrictions?.protests_count > 0 ||
    h.restrictions?.Restrictive_count > 0 ||
    h.lawsuits?.total > 0 ||
    h.fraud_alerts?.length,
  )
})

// Enabled final bureaus, list prices and the current pre-filter alert (credtech#316)
const options = createResource({
  url: 'cred_hub.credit_check.api.get_final_bureau_options',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
})

// Partners of the company (Contacts) and the queries already made (credtech#316)
const partners = createResource({
  url: 'cred_hub.credit_check.api.get_partners',
  params: { organization_name: props.organizationId },
  auto: true,
})

// Pre-select only managing/majority partners (is_admin === true) with a valid CPF by default
watch(
  () => partners.data,
  (list) => {
    if (!partnersInitialized.value && Array.isArray(list) && list.length) {
      partnersInitialized.value = true
      const admins = list
        .filter((p) => p.has_cpf && p.is_admin)
        .map((p) => p.contact)
      selected.value = admins
      reloadPackageStatus()
    }
  },
  { immediate: true },
)

const results = createResource({
  url: 'cred_hub.credit_check.api.get_bureau_results',
  params: { organization_name: props.organizationId },
  auto: true,
})

const selectedPartners = computed(() =>
  (partners.data || []).filter(
    (partner) => partner.has_cpf && selected.value.includes(partner.contact),
  ),
)

function togglePartner(contact) {
  selected.value = selected.value.includes(contact)
    ? selected.value.filter((name) => name !== contact)
    : [...selected.value, contact]
  reloadPackageStatus()
}

function selectTierMode(mode) {
  selectedTierMode.value = mode
  reloadPackageStatus()
}

// Clicking the chosen level again goes back to the company default package
function toggleTierMode(mode) {
  const active =
    mode === 'tier_2'
      ? selectedTierMode.value === 'tier_2'
      : selectedTierMode.value.startsWith('tier_3')
  selectTierMode(active ? 'default' : mode)
}

function reloadPackageStatus() {
  pkg.update({
    params: {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      selected_contacts: JSON.stringify(selected.value),
      tier:
        selectedTierMode.value === 'default' ? null : selectedTierMode.value,
    },
  })
  pkg.reload()
}

async function saveCpf(partner) {
  savingCpf.value = partner.contact
  try {
    await call('cred_hub.credit_check.api.save_partner_cpf', {
      organization_name: props.organizationId,
      contact_name: partner.contact,
      cpf: cpfDraft[partner.contact],
    })
    delete cpfDraft[partner.contact]
    await partners.reload()
    reloadPackageStatus()
    toast.success(__('CPF salvo com sucesso.'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível salvar o CPF.'))
  } finally {
    savingCpf.value = ''
  }
}

async function openResult(row) {
  try {
    const res = await call('cred_hub.credit_check.api.get_bureau_result', {
      query_name: row.name,
    })
    resultTitle.value = `${res.bureau_label} · ${res.document}`
    resultText.value = JSON.stringify(res.raw, null, 2)
    resultHtml.value = res.rendered_html || ''
    showRawJson.value = false
    showResult.value = true
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível abrir o retorno.'))
  }
}

const isReportError = computed(() => {
  const v = report.data?.verdict || org.data?.credit_verdict
  return v === 'Error'
})

const isReportSuccess = computed(() => {
  const v = report.data?.verdict || org.data?.credit_verdict
  return Boolean(v && !['Error', 'Not Checked'].includes(v))
})

function verdictText(v) {
  if (!v || v === 'Not Checked') return __('Não verificado')
  if (v === 'Pre-Approved') return __('Pré-aprovado')
  if (v === 'Warning') return __('Atenção')
  if (v === 'Rejected') return __('Reprovado')
  if (v === 'Error') return __('Falha na checagem')
  return __(v)
}

const verdictLabel = computed(() =>
  verdictText(org.data?.credit_verdict || report.data?.verdict),
)

const verdictTone = computed(() => {
  const v = org.data?.credit_verdict || report.data?.verdict
  if (v === 'Rejected' || v === 'Error') return 'error'
  if (v === 'Warning') return 'warning'
  if (v === 'Pre-Approved') return 'success'
  return 'neutral'
})

const levelOneStatus = computed(() => {
  if (isReportSuccess.value) return { label: __('Concluído'), tone: 'success' }
  if (isReportError.value)
    return { label: __('Falha na triagem'), tone: 'error' }
  return { label: __('Pendente'), tone: 'warning' }
})

// The summary explains a warning or a rejection; a clean pass needs no text
const showVerdictSummary = computed(() =>
  Boolean(
    report.data?.verdict_summary &&
    ['Warning', 'Rejected'].includes(
      org.data?.credit_verdict || report.data?.verdict,
    ),
  ),
)

const triageRows = computed(() => {
  const r = report.data || {}
  return [
    {
      label: __('Sanções CEIS/CNEP (CGU)'),
      value: r.ceis_cnep_verified
        ? r.ceis_cnep_sanctioned
          ? __('Sancionado')
          : __('Nenhuma')
        : __('Não verificado'),
      tone: r.ceis_cnep_verified && r.ceis_cnep_sanctioned ? 'error' : '',
    },
    { label: __('Regularidade FGTS (CRF)'), value: r.fgts_status || '—' },
    {
      label: __('Sintegra / Inscrição Estadual'),
      value: r.sintegra_status || '—',
    },
    { label: __('Dívida ativa na PGFN'), value: r.pgfn_status || '—' },
    {
      label: __('Processos (como réu)'),
      value: `${r.lawsuits_defendant ?? '—'} / ${r.lawsuits_total ?? '—'}`,
    },
    {
      label: __('Protestos em cartório (CENPROT)'),
      value: r.cenprot_has_protests
        ? __('{0} encontrado(s)', [r.cenprot_protests_count])
        : __('Nenhuma'),
      tone: r.cenprot_has_protests ? 'error' : '',
    },
  ]
})

const highlightGroups = computed(() => {
  const h = highlights.data || {}
  const money = (v) => (v != null ? formatMoney(v) : '—')
  const capacity = h.capacity || {}
  const restrictions = h.restrictions || {}
  const lawsuits = h.lawsuits || {}
  const capacityRows = [
    { label: __('Fat. Presumido'), value: money(capacity.presumed_revenue) },
    { label: __('Limite Sugerido'), value: money(capacity.suggested_limit) },
  ]
  if (requestedAmount.value > 0)
    capacityRows.push({
      label: __('Valor Pretendido'),
      value: formatMoney(requestedAmount.value),
      tone:
        capacity.suggested_limit &&
        requestedAmount.value > capacity.suggested_limit
          ? 'error'
          : '',
    })
  return [
    {
      key: 'scores',
      title: __('Scores de Crédito'),
      rows: (h.scores || []).map((sc) => ({
        label: sc.source,
        value: sc.band ? `${sc.value} (${sc.band})` : String(sc.value ?? '—'),
      })),
      empty: __('Nenhum score consultado ainda'),
    },
    {
      key: 'capacity',
      title: __('Capacidade & Limite (Positivo)'),
      rows: capacityRows,
      divider: true,
    },
    {
      key: 'scr',
      title: __('Endividamento Bancário (SCR)'),
      rows: h.scr
        ? [
            { label: __('Carteira Ativa'), value: money(h.scr.carteira_ativa) },
            {
              label: __('Vencido'),
              value: money(h.scr.vencido),
              tone: h.scr.vencido > 0 ? 'error' : '',
            },
            {
              label: __('Prejuízo Baixado'),
              value: money(h.scr.prejuizo),
              tone: h.scr.prejuizo > 0 ? 'error' : '',
            },
          ]
        : [],
      empty: __('SCR Bacen ainda não consultado'),
    },
    {
      key: 'restrictions',
      title: __('Protestos & Negativações'),
      rows: [
        {
          label: __('Protestos'),
          value:
            String(restrictions.protests_count || 0) +
            (restrictions.protests_total
              ? ` (${formatMoney(restrictions.protests_total)})`
              : ''),
          tone: restrictions.protests_count > 0 ? 'error' : '',
        },
        {
          label: __('Apontamentos/PEFIN'),
          value: String(restrictions.Restrictive_count || 0),
          tone: restrictions.Restrictive_count > 0 ? 'error' : '',
        },
        {
          label: __('Cheques s/ Fundo'),
          value: String(restrictions.bad_checks || 0),
          tone: restrictions.bad_checks > 0 ? 'error' : '',
        },
      ],
    },
    {
      key: 'lawsuits',
      title: __('Processos & Penhoras'),
      rows: [
        { label: __('Total Processos'), value: String(lawsuits.total || 0) },
        { label: __('Valor em Disputa'), value: money(lawsuits.total_value) },
        {
          label: __('Penhoras Ativas'),
          value: String(lawsuits.penhoras_count || 0),
          tone: lawsuits.penhoras_count > 0 ? 'error' : '',
        },
      ],
    },
    {
      key: 'punctuality',
      title: __('Pontualidade & Buscas'),
      rows: [
        {
          label: __('Pagamentos em Dia'),
          value:
            capacity.punctuality_pct != null
              ? `${capacity.punctuality_pct}%`
              : '—',
        },
        {
          label: __('Consultas (30 dias)'),
          value: String(h.inquiries_30d ?? 0),
          tone: h.inquiries_30d >= 8 ? 'error' : '',
        },
      ],
    },
  ]
})

function formatMoney(value) {
  return `R$ ${formatNumber(value)}`
}

function askRunCheck(force) {
  const reuseDays = pkg.data?.reuse_days ?? 30
  if (force && report.data?.checked_on) {
    createDialog({
      title: __('Triagem Nível 1 já realizada dentro do prazo'),
      message: __(
        'Esta empresa já foi consultada em {0}. O prazo padrão para uma nova consulta nos provedores é de {1} dias (válido até {2}). Forçar uma nova consulta agora gerará cobrança duplicada na API do provedor.',
        [report.data.checked_on, reuseDays, report.data.valid_until || '—'],
      ),
      size: 'lg',
      actions: [
        {
          label: __('Cancelar (Manter Consulta Atual)'),
          variant: 'solid',
          onClick: ({ close }) => close(),
        },
        {
          label: __('Forçar Nova Consulta Paga'),
          variant: 'outline',
          theme: 'red',
          onClick: ({ close }) => {
            close()
            runCheck(true)
          },
        },
      ],
    })
    return
  }
  runCheck(false)
}

async function runCheck(force) {
  checking.value = true
  try {
    const res = await call('cred_hub.credit_check.api.trigger_check', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      force,
      tier_1_only: 1,
    })
    if (res?.cached) {
      toast.info(res.message)
      org.reload()
      report.reload()
    } else {
      toast.success(
        __(
          'Triagem Nível 1 enviada para execução. Atualize em instantes para ver o resultado.',
        ),
      )
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível iniciar a triagem.'))
  } finally {
    checking.value = false
  }
}

const dossiers = createResource({
  url: 'cred_hub.credit_check.api.list_credit_dossiers',
  params: { organization_name: props.organizationId },
  auto: true,
})

// AI opinion (PDF 2): counter for the month, list, and polling while one is being generated
const opinionStatus = createResource({
  url: 'cred_hub.credit_check.api.get_credit_opinion_status',
  params: { organization_name: props.organizationId },
  auto: true,
})
const opinions = createResource({
  url: 'cred_hub.credit_check.api.list_credit_opinions',
  params: { organization_name: props.organizationId },
  auto: true,
})

let pollTimer = null
let pollRounds = 0

function formatPrice(value) {
  return Number(value || 0)
    .toFixed(2)
    .replace('.', ',')
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

function startPolling() {
  stopPolling()
  pollRounds = 0
  pollTimer = setInterval(async () => {
    pollRounds += 1
    await opinions.reload()
    const pending = (opinions.data || []).some(
      (item) => item.status === 'Queued',
    )
    if (!pending || pollRounds > 60) {
      stopPolling()
      opinionStatus.reload()
    }
  }, 5000)
}

onBeforeUnmount(stopPolling)

watch(
  () => opinions.data,
  (rows) => {
    if (!pollTimer && (rows || []).some((item) => item.status === 'Queued'))
      startPolling()
  },
)

// "2026-10-14 16:22:10" → "14/10/2026 16:22" (other formats pass through)
function formatDate(value) {
  if (!value) return ''
  const text = String(value)
  const m = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}:\d{2}))?/)
  if (!m) return text.slice(0, 16)
  return `${m[3]}/${m[2]}/${m[1]}${m[4] ? ' ' + m[4] : ''}`
}

function resultMeta(row) {
  const who = String(row.requested_by || '').includes('@')
    ? getUser(row.requested_by)?.full_name || row.requested_by
    : row.requested_by
  return [
    row.subject_name ? __('Sócio') : __('Empresa'),
    row.document,
    formatDate(row.requested_on),
    who,
  ]
    .filter(Boolean)
    .join(' · ')
}

// AI opinions shown under "Documentos gerados" (PDF, or the state while
// it is being generated / when it failed)
const opinionDocs = computed(() =>
  (opinions.data || []).filter(
    (item) => item.pdf_url || ['Queued', 'Failed'].includes(item.status),
  ),
)

// Minimum package of the dossier (credtech#316)
const pkg = createResource({
  url: 'cred_hub.credit_check.api.get_dossier_package_status',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
  onSuccess(data) {
    if (
      data?.deal_amount &&
      (!requestedAmount.value || requestedAmount.value <= 0)
    ) {
      requestedAmount.value = Number(data.deal_amount)
    }
  },
})
const startingPackage = ref(false)
const packageStarted = ref(false)
let pkgTimer = null
let pkgRounds = 0

const pkgRunning = computed(() =>
  Boolean(pkg.data?.running || packageStarted.value),
)

const canGeneratePackage = computed(() => {
  const data = pkg.data
  return Boolean(data && !pkgRunning.value && !data.unavailable.length)
})

function packageEntryText(entry) {
  if (entry.state === 'reused')
    return __('reaproveitado sem custo (consultado em {0})', [
      formatDate(entry.last_on),
    ])
  if (entry.state === 'unavailable')
    return __('indisponível: {0}', [entry.reason])
  return entry.price_reference
    ? __('pendente · preço de tabela {0}, cobrado por {1} na sua conta', [
        formatMoney(entry.price_reference),
        entry.provider,
      ])
    : __('pendente · cobrado por {0} na sua conta, conforme seu contrato', [
        entry.provider,
      ])
}

const packageSummary = computed(() => {
  const data = pkg.data
  if (!data) return ''
  if (!data.missing.length)
    return __(
      'Todas as consultas selecionadas já estão em dia. Gerar o dossiê não consumirá novas consultas pagas.',
    )
  let text = __(
    'Para gerar neste nível: {0} consulta(s) paga(s), cerca de {1} pelo preço de tabela, cobrado pelo provedor na sua conta.',
    [data.missing.length, formatMoney(data.missing_cost)],
  )
  if (data.missing_has_contract_price)
    text += ' ' + __('A Serasa é cobrada conforme o seu contrato.')
  return text
})

const opinionNote = computed(() => {
  const opinion = pkg.data?.opinion
  if (!opinion) return ''
  if (!opinion.configured)
    return __(
      'O dossiê será gerado sem o parecer da IA (IA ainda não configurada neste site).',
    )
  if (opinion.next_is_extra && !opinion.extra_allowed)
    return __(
      'O dossiê será gerado sem o parecer da IA: a franquia mensal acabou. Um administrador pode liberar pareceres extras (R$ {0} cada) nas Configurações.',
      [formatPrice(opinion.extra_price)],
    )
  if (opinion.next_is_extra)
    return __(
      'O parecer da IA será avulso neste mês: R$ {0} da carteira de créditos.',
      [formatPrice(opinion.extra_price)],
    )
  return ''
})

function stopPackagePolling() {
  if (pkgTimer) clearInterval(pkgTimer)
  pkgTimer = null
}

function startPackagePolling() {
  stopPackagePolling()
  pkgRounds = 0
  pkgTimer = setInterval(async () => {
    pkgRounds += 1
    await pkg.reload()
    if (!pkg.data?.running || pkgRounds > 120) {
      packageStarted.value = false
      stopPackagePolling()
      dossiers.reload()
      results.reload()
      highlights.reload()
      opinions.reload()
      opinionStatus.reload()
    }
  }, 5000)
}

onBeforeUnmount(stopPackagePolling)

const requestingOpinion = ref(false)

const groupedDossiers = computed(() => {
  const list = dossiers.data || []
  const groups = []
  const byStamp = {}
  for (const file of list) {
    const name = file.file_name || ''
    const isPdf = name.endsWith('.pdf')
    const isJson = name.endsWith('.json')
    const stampKey = String(file.creation || '').slice(0, 16)
    if (!byStamp[stampKey]) {
      byStamp[stampKey] = {
        key: stampKey,
        creation: file.creation,
        pdf: null,
        json: null,
      }
      groups.push(byStamp[stampKey])
    }
    if (isPdf && !byStamp[stampKey].pdf) byStamp[stampKey].pdf = file
    if (isJson && !byStamp[stampKey].json) byStamp[stampKey].json = file
  }
  return groups.filter((g) => g.pdf || g.json)
})

async function askOpinionOnly() {
  const opinion = pkg.data?.opinion || opinionStatus.data || {}
  const extraOpinion =
    opinion.configured && opinion.next_is_extra && opinion.extra_allowed
  if (extraOpinion) {
    createDialog({
      title: __('Gerar Parecer de Crédito (IA)'),
      message: __(
        'Os pareceres incluídos no mês acabaram. Este parecer avulso custa R$ {0} da carteira de créditos.',
        [formatPrice(opinion.extra_price)],
      ),
      actions: [
        { label: __('Cancelar'), onClick: ({ close }) => close() },
        {
          label: __('Confirmar e Gerar Parecer IA'),
          variant: 'solid',
          onClick: ({ close }) => {
            close()
            triggerOpinionOnly(true)
          },
        },
      ],
    })
    return
  }
  triggerOpinionOnly(false)
}

async function triggerOpinionOnly(confirmExtra) {
  requestingOpinion.value = true
  try {
    await call('cred_hub.credit_check.api.request_credit_opinion', {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      confirm_extra_cost: confirmExtra ? 1 : 0,
      requested_amount: requestedAmount.value || null,
    })
    toast.success(
      __(
        'Parecer Executivo de Crédito (IA) enviado para geração em segundo plano. Aguarde alguns instantes.',
      ),
    )
    await opinions.reload()
    startPolling()
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível solicitar o parecer da IA.'),
    )
  } finally {
    requestingOpinion.value = false
  }
}

function askPackage() {
  const data = pkg.data
  if (!data) return
  const opinion = data.opinion || {}
  const extraOpinion =
    opinion.configured && opinion.next_is_extra && opinion.extra_allowed
  const needsAck = Boolean(data.needs_acknowledgement)
  if (!data.missing.length && !extraOpinion) {
    createDialog({
      title: __('Consultas em dia (Prazo de {0} dias)', [
        data.reuse_days || 30,
      ]),
      message: __(
        'Todas as consultas selecionadas para esta empresa já foram realizadas recentemente. O prazo configurado para novas consultas na API do provedor é de {0} dias. Nenhuma nova consulta paga será disparada no provedor.',
        [data.reuse_days || 30],
      ),
      size: 'xl',
      actions: [
        { label: __('Cancelar'), onClick: ({ close }) => close() },
        {
          label: __('Reprocessar Parecer IA'),
          variant: 'outline',
          onClick: ({ close }) => {
            close()
            triggerOpinionOnly(false)
          },
        },
        {
          label: __('Atualizar Dossiê PDF'),
          variant: 'solid',
          onClick: ({ close }) => {
            close()
            generatePackage(false, false)
          },
        },
      ],
    })
    return
  }
  const lines = []
  if (data.missing.length) {
    lines.push(
      __('Consultas pagas, cobradas pelo provedor na sua conta: {0}.', [
        data.missing
          .map((entry) => `${entry.label} (${entry.subject_name})`)
          .join(', '),
      ]),
    )
    lines.push(
      __('Cerca de {0} pelo preço de tabela.', [
        formatMoney(data.missing_cost),
      ]),
    )
  }
  if (needsAck) {
    lines.push(
      __('Alerta: o resultado da triagem rápida para esta organização é {0}.', [
        verdictText(data.verdict),
      ]) +
        (data.verdict_summary ? ' ' + data.verdict_summary : '') +
        ' ' +
        __('A consulta ficará registrada como realizada sob alerta.'),
    )
  }
  if (extraOpinion) {
    lines.push(
      __(
        'Os pareceres incluídos no mês acabaram. Este parecer custa R$ {0} da carteira de créditos (saldo atual R$ {1}).',
        [formatPrice(opinion.extra_price), formatPrice(opinion.balance)],
      ),
    )
  }
  createDialog({
    title: __('Gerar dossiê de crédito'),
    message: lines.join(' '),
    size: 'lg',
    actions: [
      { label: __('Cancelar'), onClick: ({ close }) => close() },
      {
        label: needsAck
          ? __('Consultar mesmo assim e gerar')
          : __('Confirmar e gerar'),
        variant: 'solid',
        theme: needsAck ? 'red' : 'gray',
        onClick: ({ close }) => {
          close()
          generatePackage(needsAck, extraOpinion)
        },
      },
    ],
  })
}

async function generatePackage(acknowledged, confirmExtra) {
  startingPackage.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.generate_credit_package',
      {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        confirm_cost: 1,
        acknowledged_warning: acknowledged ? 1 : 0,
        confirm_extra_cost: confirmExtra ? 1 : 0,
        selected_contacts: JSON.stringify(selected.value),
        tier:
          selectedTierMode.value === 'default' ? null : selectedTierMode.value,
        requested_amount: requestedAmount.value || null,
      },
    )
    packageStarted.value = true
    if (res?.opinion_skipped) {
      toast.warning(
        __('Gerando dossiê sem o parecer da IA: {0}', [res.opinion_skipped]),
      )
    } else {
      toast.success(
        __(
          'Gerando o dossiê: as consultas, o PDF 1 e o parecer da IA levam alguns instantes.',
        ),
      )
    }
    opinions.reload()
    startPackagePolling()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível gerar o dossiê.'))
    pkg.reload()
  } finally {
    startingPackage.value = false
  }
}

function askPremiumBureau(bureau, partnerList = []) {
  const data = options.data
  const needsAck = Boolean(data?.needs_acknowledgement)
  const count = partnerList.length || 1
  const recent = !partnerList.length ? bureau.recent_company_query : null

  if (recent) {
    createDialog({
      title: __('Consulta já realizada ({0})', [bureau.label]),
      message: __(
        'Esta consulta já foi realizada em {0}. O prazo configurado para nova consulta é de {1} dias (válido até {2}). Consultar novamente agora gerará uma cobrança duplicada na sua conta do provedor ({3}).',
        [
          formatDate(recent.requested_on),
          recent.reuse_days || 30,
          recent.valid_until || '—',
          bureau.provider,
        ],
      ),
      size: 'lg',
      actions: [
        {
          label: __('Cancelar (Não Cobrar Novamente)'),
          variant: 'solid',
          onClick: ({ close }) => close(),
        },
        {
          label: __('Forçar Nova Consulta Paga Mesmo Assim'),
          variant: 'outline',
          theme: 'red',
          onClick: ({ close }) => {
            close()
            requestPremiumBureau(bureau.key, needsAck, [], true)
          },
        },
      ],
    })
    return
  }
  let message = bureau.price_reference
    ? __(
        'Esta consulta é paga e cobrada por {0} na sua conta (preço de tabela {1}).',
        [bureau.provider, formatMoney(bureau.price_reference)],
      )
    : __(
        'Esta consulta é paga e cobrada por {0} na sua conta, conforme seu contrato.',
        [bureau.provider],
      )
  if (partnerList.length) {
    message +=
      ' ' +
      __('Sócios selecionados: {0}. {1} consulta(s)', [
        partnerList.map((partner) => partner.name).join(', '),
        count,
      ]) +
      (bureau.price_reference
        ? ' ' +
          __('(cerca de {0} no total pelo preço de tabela).', [
            formatMoney(bureau.price_reference * count),
          ])
        : '.')
  }
  if (needsAck) {
    message +=
      ' ' +
      __('Alerta: o resultado da triagem rápida para esta organização é {0}.', [
        verdictText(data.verdict),
      ]) +
      (data.verdict_summary ? ' ' + data.verdict_summary : '') +
      ' ' +
      __('A consulta ficará registrada como realizada sob alerta.')
  }
  createDialog({
    title: bureau.label,
    message,
    size: 'lg',
    actions: [
      {
        label: __('Cancelar'),
        onClick: ({ close }) => close(),
      },
      {
        label: needsAck
          ? __('Consultar mesmo assim (pago)')
          : __('Confirmar consulta paga'),
        variant: 'solid',
        theme: needsAck ? 'red' : 'gray',
        onClick: ({ close }) => {
          close()
          requestPremiumBureau(
            bureau.key,
            needsAck,
            partnerList.map((partner) => partner.contact),
          )
        },
      },
    ],
  })
}

// "Bureaus para os sócios marcados": PF bureaus run for every checked partner
const partnerBureauKeys = ref([])
const partnerBureaus = computed(() =>
  (options.data?.bureaus || []).filter((bureau) => bureau.partner_ok),
)
const chosenPartnerBureaus = computed(() =>
  partnerBureaus.value.filter(
    (bureau) =>
      bureau.configured && partnerBureauKeys.value.includes(bureau.key),
  ),
)
const canRunPartnerBureaus = computed(() =>
  Boolean(
    options.data?.can_request &&
    selectedPartners.value.length &&
    chosenPartnerBureaus.value.length &&
    !requesting.value,
  ),
)

function togglePartnerBureau(key) {
  partnerBureauKeys.value = partnerBureauKeys.value.includes(key)
    ? partnerBureauKeys.value.filter((k) => k !== key)
    : [...partnerBureauKeys.value, key]
}

function askPartnerBureaus() {
  const bureaus = chosenPartnerBureaus.value
  const partnerList = selectedPartners.value
  if (!bureaus.length || !partnerList.length) return
  if (bureaus.length === 1) return askPremiumBureau(bureaus[0], partnerList)
  const data = options.data
  const needsAck = Boolean(data?.needs_acknowledgement)
  const count = bureaus.length * partnerList.length
  const priced = bureaus.every((bureau) => bureau.price_reference)
  const total = bureaus.reduce(
    (sum, bureau) => sum + (bureau.price_reference || 0) * partnerList.length,
    0,
  )
  let message =
    __('Consultas pagas, cobradas pelo provedor na sua conta: {0}.', [
      bureaus
        .map((bureau) => `${bureau.label} (${bureau.provider})`)
        .join(', '),
    ]) +
    ' ' +
    __('Sócios selecionados: {0}. {1} consulta(s)', [
      partnerList.map((partner) => partner.name).join(', '),
      count,
    ]) +
    (priced
      ? ' ' +
        __('(cerca de {0} no total pelo preço de tabela).', [
          formatMoney(total),
        ])
      : '.')
  if (needsAck) {
    message +=
      ' ' +
      __('Alerta: o resultado da triagem rápida para esta organização é {0}.', [
        verdictText(data.verdict),
      ]) +
      (data.verdict_summary ? ' ' + data.verdict_summary : '') +
      ' ' +
      __('A consulta ficará registrada como realizada sob alerta.')
  }
  createDialog({
    title: __('Gerar bureaus dos sócios'),
    message,
    size: 'lg',
    actions: [
      { label: __('Cancelar'), onClick: ({ close }) => close() },
      {
        label: needsAck
          ? __('Consultar mesmo assim (pago)')
          : __('Confirmar consulta paga'),
        variant: 'solid',
        theme: needsAck ? 'red' : 'gray',
        onClick: async ({ close }) => {
          close()
          const contacts = partnerList.map((partner) => partner.contact)
          for (const bureau of bureaus) {
            await requestPremiumBureau(bureau.key, needsAck, contacts)
          }
        },
      },
    ],
  })
}

async function requestPremiumBureau(
  bureau,
  acknowledged,
  contacts = [],
  forceRequery = false,
) {
  requesting.value = contacts.length ? bureau + ':partners' : bureau
  const targets = contacts.length ? contacts : [null]
  let done = 0
  const failures = []
  for (const contact of targets) {
    try {
      await call('cred_hub.credit_check.api.request_bureau_final', {
        organization_name: props.organizationId,
        deal_name: props.dealId || null,
        bureau,
        confirm_cost: 1,
        acknowledged_warning: acknowledged ? 1 : 0,
        contact_name: contact,
        force_requery: forceRequery ? 1 : 0,
      })
      done += 1
    } catch (err) {
      failures.push(
        err?.messages?.[0] ||
          err?.message ||
          __('Não foi possível solicitar a consulta.'),
      )
    }
  }
  if (done) {
    toast.success(
      targets.length > 1
        ? __('{0} de {1} consultas solicitadas.', [done, targets.length])
        : __('Consulta realizada com sucesso.'),
    )
  }
  failures.forEach((message) => toast.error(message))
  report.reload()
  options.reload()
  results.reload()
  highlights.reload()
  reloadPackageStatus()
  requesting.value = ''
}

// The deal top bar ("Gerar parecer de IA") drives the AI opinion from here
defineExpose({
  askOpinionOnly,
  requestingOpinion,
  opinionConfigured: computed(() => Boolean(opinionStatus.data?.configured)),
  opinionUsage: computed(() =>
    opinionStatus.data
      ? __('{0} de {1} pareceres usados neste mês', [
          opinionStatus.data.used,
          opinionStatus.data.included,
        ])
      : '',
  ),
})
</script>
