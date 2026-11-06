<template>
  <div class="flex flex-col gap-6 p-5 max-w-4xl">
    <!-- ===================================================================== -->
    <!-- TOP FUNNEL BAR: 3 NÍVEIS PROGRESSIVOS + VALOR PRETENDIDO DA OPERAÇÃO  -->
    <!-- ===================================================================== -->
    <div
      class="flex flex-col gap-4 p-4 bg-surface-white rounded-xl border border-outline-gray-2 shadow-sm"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-base font-semibold text-[#1E1F23]">
              {{ __('Esteira Progressiva de Análise de Crédito (3 Níveis)') }}
            </span>
            <Badge
              :label="__('Zero Redundância')"
              theme="blue"
              variant="subtle"
            />
          </div>
          <p class="text-p-xs text-[#5E6068] mt-0.5">
            {{
              __(
                'Avance conforme o ticket da operação para proteger o custo de API da sua conta nos bureaus.',
              )
            }}
          </p>
        </div>

        <!-- Valor Pretendido da Operação -->
        <div class="flex items-center gap-2 bg-[#F5F5F7] px-3 py-2 rounded-lg border border-[#E6E7EB]">
          <div class="text-xs font-medium text-[#5E6068]">
            {{ __('Valor Pretendido (R$):') }}
          </div>
          <input
            v-model.number="requestedAmount"
            type="number"
            min="0"
            step="1000"
            :placeholder="__('Ex: 50000')"
            class="w-36 h-8 px-2.5 text-sm font-semibold text-[#1E1F23] bg-white border border-[#DCDDE2] rounded-md focus:outline-none focus:border-[#0088FF]"
          />
          <Badge
            v-if="recommendedTierBadge"
            :theme="recommendedTierBadge.theme"
            variant="subtle"
            :label="recommendedTierBadge.label"
          />
        </div>
      </div>

      <!-- 3 Steps Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <!-- Nível 1 -->
        <div
          class="p-3 rounded-lg border transition-colors"
          :class="
            report.data
              ? 'border-[#1F7A3D]/30 bg-[#E7F6EC]/40'
              : 'border-[#E6E7EB] bg-[#F5F5F7]/60'
          "
        >
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-[#1E1F23]">
              {{ __('1. Nível Inicial · Triagem') }}
            </span>
            <Badge
              :label="report.data ? __('Concluído') : __('R$ 0,00 a R$ 0,72')"
              :theme="report.data ? 'green' : 'gray'"
              variant="subtle"
            />
          </div>
          <p class="text-p-xs text-[#5E6068]">
            {{
              __(
                'Receita Federal/QSA + CGU CEIS/CNEP (Grátis) + Sintegra UF (R$ 0,36) + FGTS (R$ 0,36). Elimina empresas inaptas ou sancionadas na largada.',
              )
            }}
          </p>
        </div>

        <!-- Nível 2 -->
        <div
          class="p-3 rounded-lg border transition-colors cursor-pointer"
          :class="
            selectedTierMode === 'tier_2'
              ? 'border-[#0088FF] bg-[#E5F1FF]/50'
              : 'border-[#E6E7EB] bg-[#F5F5F7]/60 hover:border-[#DCDDE2]'
          "
          @click="selectTierMode('tier_2')"
        >
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-[#1E1F23]">
              {{ __('2. Nível Médio · Dossiê Base') }}
            </span>
            <Badge
              :label="__('R$ 10,89 PJ')"
              theme="blue"
              variant="subtle"
            />
          </div>
          <p class="text-p-xs text-[#5E6068]">
            {{
              __(
                'Dossiê QUOD Completo (Score + Protestos + Ações + Cheques) + SCR Bacen. Ideal para tickets pequenos e médios.',
              )
            }}
          </p>
        </div>

        <!-- Nível 3 -->
        <div
          class="p-3 rounded-lg border transition-colors cursor-pointer"
          :class="
            selectedTierMode.startsWith('tier_3')
              ? 'border-[#0088FF] bg-[#E5F1FF]/50'
              : 'border-[#E6E7EB] bg-[#F5F5F7]/60 hover:border-[#DCDDE2]'
          "
          @click="selectTierMode('tier_3_boavista')"
        >
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-[#1E1F23]">
              {{ __('3. Nível Profundo · Alto Ticket') }}
            </span>
            <Badge
              :label="__('Positivo + Penhoras + Sócios')"
              theme="amber"
              variant="subtle"
            />
          </div>
          <p class="text-p-xs text-[#5E6068]">
            {{
              __(
                'Boa Vista Risco Positivo PJ (ou Serasa) + SCR Bacen + Processos c/ Penhoras + Sócios PF. Pule direto do Nível 1 para cá em operações maiores.',
              )
            }}
          </p>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- NÍVEL 1: TRIAGEM JURÍDICA, CADASTRAL & FISCAL (PRÉ-FILTRO BARATO)     -->
    <!-- ===================================================================== -->
    <div
      class="flex flex-col gap-3 p-4 bg-surface-gray-2 rounded-lg border border-outline-gray-2"
    >
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-3">
            <span class="text-base font-semibold text-ink-gray-9">
              {{ __('Nível 1 · Triagem Cadastral, Fiscal & Compliance') }}
            </span>
            <Badge :theme="verdictTheme" variant="solid" size="lg">
              {{ verdictLabel }}
            </Badge>
            <span v-if="org.data?.cnpj" class="text-p-sm text-ink-gray-6">
              {{ __('CNPJ') }} {{ org.data?.cnpj }}
            </span>
          </div>
          <p class="text-p-xs text-ink-gray-6">
            {{
              __(
                'Checagem imediata de Situação Cadastral/QSA, Sanções Públicas CEIS/CNEP (CGU · Grátis), Sintegra/CCC por UF, Regularidade FGTS e Dívida Ativa PGFN antes de consultar bureaus de crédito.',
              )
            }}
          </p>
        </div>
        <div class="flex gap-2 items-center">
          <Button
            v-if="!org.data?.credit_report"
            variant="solid"
            :loading="checking"
            @click="askRunCheck(false)"
          >
            {{ __('Executar Triagem Nível 1') }}
          </Button>
          <Button
            v-else
            variant="outline"
            :loading="checking"
            @click="askRunCheck(true)"
          >
            {{ __('Atualizar Triagem Nível 1') }}
          </Button>
        </div>
      </div>
      <div
        v-if="report.data?.checked_on"
        class="flex flex-wrap items-center justify-between gap-2 text-p-xs text-ink-green-3 bg-surface-white px-3 py-1.5 rounded border border-outline-gray-1"
      >
        <span>
          ✓ {{ __('Triagem já realizada em {0} · Prazo para nova consulta: {1} dias (válido até {2})', [
            report.data.checked_on,
            pkg.data?.reuse_days ?? 30,
            report.data.valid_until || '—',
          ]) }}
        </span>
        <span class="text-ink-gray-5">
          {{ __('Prazo alterável em Configurações > Bureaus e Crédito') }}
        </span>
      </div>
      <div
        v-if="report.data?.verdict_summary"
        class="text-p-xs text-ink-gray-7 bg-surface-white px-3 py-2 rounded border border-outline-gray-1"
      >
        {{ report.data.verdict_summary }}
      </div>
    </div>

    <p v-if="!org.data?.credit_report" class="text-p-sm text-ink-gray-5">
      {{ __('Nenhuma triagem jurídica/fiscal foi executada para esta organização ainda.') }}
    </p>

    <template v-if="report.data">
      <!-- Summary Nível 1 -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">
            {{ __('Sanções CEIS/CNEP (CGU)') }}
          </div>
          <div
            class="text-base-medium"
            :class="
              !report.data.ceis_cnep_verified
                ? 'text-ink-gray-6'
                : report.data.ceis_cnep_sanctioned
                  ? 'text-ink-red-3'
                  : 'text-ink-green-3'
            "
          >
            {{
              report.data.ceis_cnep_verified
                ? report.data.ceis_cnep_sanctioned
                  ? __('Sancionado')
                  : __('Nenhuma')
                : __('Não verificado')
            }}
          </div>
        </div>
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">{{ __('Regularidade FGTS (CRF)') }}</div>
          <div class="text-base-medium">
            {{ report.data.fgts_status || '—' }}
          </div>
        </div>
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">{{ __('Sintegra / Inscrição Estadual') }}</div>
          <div class="text-base-medium">
            {{ report.data.sintegra_status || '—' }}
          </div>
        </div>
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">
            {{ __('Dívida ativa na PGFN') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.pgfn_status || '—' }}
          </div>
        </div>
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">
            {{ __('Processos (como réu)') }}
          </div>
          <div class="text-base-medium">
            {{ report.data.lawsuits_defendant ?? '—' }} /
            {{ report.data.lawsuits_total ?? '—' }}
          </div>
        </div>
        <div class="p-3.5 border border-outline-gray-2 rounded-lg space-y-1 bg-surface-white">
          <div class="text-p-xs text-ink-gray-5">
            {{ __('Protestos em cartório (CENPROT)') }}
          </div>
          <div
            class="text-base-medium"
            :class="
              report.data.cenprot_has_protests
                ? 'text-ink-red-3'
                : 'text-ink-green-3'
            "
          >
            {{
              report.data.cenprot_has_protests
                ? __('{0} encontrado(s)', [report.data.cenprot_protests_count])
                : __('Nenhuma')
            }}
          </div>
        </div>
      </div>
    </template>

    <!-- ===================================================================== -->
    <!-- VISÃO EXECUTIVA CONSOLIDADA DOS BUREAUS + ALERTAS DE FRAUDE           -->
    <!-- ===================================================================== -->
    <div
      v-if="hasHighlights"
      class="p-5 bg-surface-white rounded-xl border border-outline-gray-2 space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span class="text-lg-semibold text-[#1E1F23]">
            {{ __('Resumo Executivo Unificado dos Bureaus') }}
          </span>
          <p class="text-p-xs text-[#5E6068]">
            {{
              __(
                'Indicadores consolidados automaticamente a partir das consultas realizadas (QUOD, Boa Vista, Serasa, SCR Bacen e Processos).',
              )
            }}
          </p>
        </div>
        <Badge
          :label="__('Visão Consolidada')"
          theme="blue"
          variant="subtle"
        />
      </div>

      <!-- Fraud Alerts / Red Flags -->
      <div
        v-if="highlights.data?.fraud_alerts?.length"
        class="space-y-2"
      >
        <div
          v-for="(alert, idx) in highlights.data.fraud_alerts"
          :key="idx"
          class="p-3 rounded-lg border text-p-sm flex items-start gap-2.5"
          :class="
            alert.severity === 'critical'
              ? 'bg-[#FEF3F2] border-[#B42318]/30 text-[#B42318]'
              : 'bg-[#FFF4D6] border-[#8A5A00]/30 text-[#8A5A00]'
          "
        >
          <span class="font-bold">⚠️</span>
          <div class="space-y-0.5">
            <div class="font-semibold">{{ alert.title }}</div>
            <div class="text-p-xs opacity-90">{{ alert.detail }}</div>
          </div>
        </div>
      </div>

      <!-- 6 Consolidated KPI Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <!-- 1. Scores -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Scores de Crédito') }}
          </div>
          <div v-if="highlights.data?.scores?.length" class="space-y-1">
            <div
              v-for="sc in highlights.data.scores"
              :key="sc.source"
              class="flex items-center justify-between text-p-sm"
            >
              <span class="text-[#5E6068]">{{ sc.source }}:</span>
              <span class="font-bold text-[#1E1F23]">
                {{ sc.value }}
                <span v-if="sc.band" class="text-xs font-normal text-[#5E6068]">({{ sc.band }})</span>
              </span>
            </div>
          </div>
          <div v-else class="text-p-xs text-[#8A8C94]">
            {{ __('Nenhum score consultado ainda') }}
          </div>
        </div>

        <!-- 2. Capacidade & Limite vs Operação -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Capacidade & Limite (Positivo)') }}
          </div>
          <div class="space-y-1 text-p-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Fat. Presumido:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{
                  highlights.data?.capacity?.presumed_revenue != null
                    ? formatMoney(highlights.data.capacity.presumed_revenue)
                    : '—'
                }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Limite Sugerido:') }}</span>
              <span class="font-semibold text-[#0088FF]">
                {{
                  highlights.data?.capacity?.suggested_limit != null
                    ? formatMoney(highlights.data.capacity.suggested_limit)
                    : '—'
                }}
              </span>
            </div>
            <div
              v-if="requestedAmount > 0"
              class="flex items-center justify-between pt-1 border-t border-[#E6E7EB]"
            >
              <span class="text-[#5E6068]">{{ __('Valor Pretendido:') }}</span>
              <span
                class="font-bold"
                :class="
                  highlights.data?.capacity?.suggested_limit &&
                  requestedAmount > highlights.data.capacity.suggested_limit
                    ? 'text-[#B42318]'
                    : 'text-[#1F7A3D]'
                "
              >
                {{ formatMoney(requestedAmount) }}
              </span>
            </div>
          </div>
        </div>

        <!-- 3. Endividamento SCR Bacen -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Endividamento Bancário (SCR)') }}
          </div>
          <div v-if="highlights.data?.scr" class="space-y-1 text-p-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Carteira Ativa:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{ formatMoney(highlights.data.scr.carteira_ativa) }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Vencido:') }}</span>
              <span
                class="font-semibold"
                :class="highlights.data.scr.vencido > 0 ? 'text-[#B42318]' : 'text-[#1F7A3D]'"
              >
                {{ formatMoney(highlights.data.scr.vencido) }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Prejuízo Baixado:') }}</span>
              <span
                class="font-semibold"
                :class="highlights.data.scr.prejuizo > 0 ? 'text-[#B42318]' : 'text-[#1E1F23]'"
              >
                {{ formatMoney(highlights.data.scr.prejuizo) }}
              </span>
            </div>
          </div>
          <div v-else class="text-p-xs text-[#8A8C94]">
            {{ __('SCR Bacen ainda não consultado') }}
          </div>
        </div>

        <!-- 4. Protestos & Negativações -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Protestos & Negativações') }}
          </div>
          <div class="space-y-1 text-p-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Protestos:') }}</span>
              <span
                class="font-semibold"
                :class="highlights.data?.restrictions?.protests_count > 0 ? 'text-[#B42318]' : 'text-[#1F7A3D]'"
              >
                {{ highlights.data?.restrictions?.protests_count || 0 }}
                <span v-if="highlights.data?.restrictions?.protests_total">
                  ({{ formatMoney(highlights.data.restrictions.protests_total) }})
                </span>
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Apontamentos/PEFIN:') }}</span>
              <span
                class="font-semibold"
                :class="highlights.data?.restrictions?.Restrictive_count > 0 ? 'text-[#B42318]' : 'text-[#1F7A3D]'"
              >
                {{ highlights.data?.restrictions?.Restrictive_count || 0 }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Cheques s/ Fundo:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{ highlights.data?.restrictions?.bad_checks || 0 }}
              </span>
            </div>
          </div>
        </div>

        <!-- 5. Processos Judiciais & Penhoras -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Processos & Penhoras') }}
          </div>
          <div class="space-y-1 text-p-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Total Processos:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{ highlights.data?.lawsuits?.total || 0 }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Valor em Disputa:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{ formatMoney(highlights.data?.lawsuits?.total_value || 0) }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Penhoras Ativas:') }}</span>
              <span
                class="font-bold"
                :class="highlights.data?.lawsuits?.penhoras_count > 0 ? 'text-[#B42318]' : 'text-[#1F7A3D]'"
              >
                {{ highlights.data?.lawsuits?.penhoras_count || 0 }}
              </span>
            </div>
          </div>
        </div>

        <!-- 6. Pontualidade / Consultas Recentes -->
        <div class="p-3.5 rounded-lg border border-[#E6E7EB] bg-[#F5F5F7]/50 space-y-1.5">
          <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
            {{ __('Pontualidade & Buscas') }}
          </div>
          <div class="space-y-1 text-p-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Pagamentos em Dia:') }}</span>
              <span class="font-semibold text-[#1E1F23]">
                {{
                  highlights.data?.capacity?.punctuality_pct != null
                    ? `${highlights.data.capacity.punctuality_pct}%`
                    : '—'
                }}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[#5E6068]">{{ __('Consultas (30 dias):') }}</span>
              <span
                class="font-semibold"
                :class="highlights.data?.inquiries_30d >= 8 ? 'text-[#B42318]' : 'text-[#1E1F23]'"
              >
                {{ highlights.data?.inquiries_30d ?? 0 }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- QUADRO SOCIETÁRIO (PRÉ-SELEÇÃO DO SÓCIO-ADMINISTRADOR P/ ECONOMIA)   -->
    <!-- ===================================================================== -->
    <div
      v-if="partners.data && partners.data.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div>
          <span class="text-lg-semibold text-ink-gray-9">{{
            __('Quadro Societário (Seleção de Sócios para Consulta PF)')
          }}</span>
          <p class="text-p-xs text-ink-gray-6 mt-0.5">
            {{
              __(
                'Por padrão, pré-selecionamos apenas o(s) Sócio(s)-Administrador(es) para evitar cobrança multiplicada em sócios minoritários. Marque ou desmarque quem deseja consultar no Dossiê ou em consultas avulsas.',
              )
            }}
          </p>
        </div>
        <Badge
          :label="__('{0} sócio(s) selecionado(s)', [selectedPartners.length])"
          theme="blue"
          variant="subtle"
        />
      </div>

      <div
        v-for="partner in partners.data"
        :key="partner.contact"
        class="flex items-center justify-between p-3 border border-outline-gray-2 rounded gap-3"
      >
        <div class="flex items-center gap-3 min-w-0">
          <input
            type="checkbox"
            class="size-4 accent-[#0088FF]"
            :checked="selected.includes(partner.contact)"
            :disabled="!partner.has_cpf"
            @change="togglePartner(partner.contact)"
          />
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-base-medium truncate">{{ partner.name }}</span>
              <Badge
                v-if="partner.is_admin"
                :label="__('Sócio-Administrador')"
                theme="blue"
                variant="subtle"
              />
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{ partner.designation }}
              <span v-if="partner.share != null"> · {{ partner.share }}%</span>
            </div>
          </div>
        </div>
        <div v-if="partner.has_cpf" class="text-p-sm text-ink-gray-7 font-mono">
          {{ partner.cpf }}
        </div>
        <div v-else class="flex items-center gap-2">
          <FormControl
            v-model="cpfDraft[partner.contact]"
            type="text"
            class="w-40"
            :placeholder="__('CPF completo')"
          />
          <Button
            variant="outline"
            size="sm"
            :loading="savingCpf === partner.contact"
            :disabled="!cpfDraft[partner.contact]"
            @click="saveCpf(partner)"
          >
            {{ __('Salvar CPF') }}
          </Button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- DOSSIÊ DE CRÉDITO COMPLETO (ESCOLHA DE NÍVEL 2 OU NÍVEL 3 + PDF 1/2) -->
    <!-- ===================================================================== -->
    <div
      v-if="pkg.data"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg-semibold text-ink-gray-9">{{
            __('Gerar Dossiê de Crédito (Nível 2 Médio ou Nível 3 Profundo)')
          }}</span>
          <Badge
            v-if="pkgRunning"
            theme="blue"
            variant="subtle"
            :label="__('Gerando…')"
          />
        </div>

        <!-- Seletor Rápido de Nível -->
        <div class="flex flex-wrap items-center gap-1.5">
          <Button
            :variant="selectedTierMode === 'default' ? 'solid' : 'subtle'"
            size="sm"
            @click="selectTierMode('default')"
          >
            {{ __('Padrão da Empresa') }}
          </Button>
          <Button
            :variant="selectedTierMode === 'tier_2' ? 'solid' : 'subtle'"
            size="sm"
            @click="selectTierMode('tier_2')"
          >
            {{ __('Nível 2 · Médio (QUOD + SCR)') }}
          </Button>
          <Button
            :variant="selectedTierMode === 'tier_3_boavista' ? 'solid' : 'subtle'"
            size="sm"
            @click="selectTierMode('tier_3_boavista')"
          >
            {{ __('Nível 3 · Boa Vista Positivo') }}
          </Button>
          <Button
            :variant="selectedTierMode === 'tier_3_serasa' ? 'solid' : 'subtle'"
            size="sm"
            @click="selectTierMode('tier_3_serasa')"
          >
            {{ __('Nível 3 · Serasa Avançado') }}
          </Button>
        </div>
      </div>

      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Executa apenas as consultas que faltam no nível selecionado (reaproveitando consultas dos últimos {0} dias sem novo custo, como o SCR Bacen), gera o PDF 1 (Relatório Executivo Formatado) e o PDF 2 (Parecer Estruturado da IA em 6 Seções).',
            [pkg.data.reuse_days],
          )
        }}
      </p>

      <div class="space-y-1.5 bg-[#F5F5F7] p-3.5 rounded-lg border border-[#E6E7EB]">
        <div class="text-xs font-semibold uppercase tracking-wider text-[#5E6068]">
          {{ __('Consultas incluídas nesta execução') }}
        </div>
        <div
          v-for="entry in pkg.data.items"
          :key="entry.item + (entry.contact || '')"
          class="flex items-start gap-2 text-p-sm"
        >
          <span
            :class="
              entry.state === 'reused'
                ? 'text-ink-green-3 font-bold'
                : entry.state === 'unavailable'
                  ? 'text-ink-red-3 font-bold'
                  : 'text-[#0088FF] font-bold'
            "
            >{{ entry.state === 'reused' ? '✓' : '•' }}</span
          >
          <div>
            <span class="text-ink-gray-8 font-medium"
              >{{ entry.label }} · {{ entry.subject_name }}</span
            >
            <span class="text-ink-gray-5">
              — {{ packageEntryText(entry) }}</span
            >
            <div v-if="entry.last_error" class="text-ink-red-3">
              {{ __('Última tentativa falhou: {0}', [entry.last_error]) }}
            </div>
          </div>
        </div>
        <div
          v-if="pkg.data.partners_without_cpf.length"
          class="text-p-xs text-ink-gray-5 pt-1"
        >
          {{
            __('Sócios sem CPF completo ficam de fora do pacote: {0}.', [
              pkg.data.partners_without_cpf.join(', '),
            ])
          }}
        </div>
      </div>

      <div class="text-p-sm font-medium text-ink-gray-8">{{ packageSummary }}</div>
      <div v-if="pkg.data.unavailable.length" class="text-p-sm text-ink-red-3">
        {{
          __(
            'Um administrador precisa habilitar e configurar o token destes bureaus ou retirá-los do pacote em Configurações > Bureaus e Crédito.',
          )
        }}
      </div>
      <div v-if="opinionNote" class="text-p-sm text-[color:var(--ct-warning)] font-medium">
        {{ opinionNote }}
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="solid"
          :loading="startingPackage"
          :disabled="!canGeneratePackage"
          @click="askPackage"
        >
          {{ __('Gerar Dossiê Completo (PDF Formatado + Parecer IA)') }}
        </Button>
      </div>
      <div v-if="groupedDossiers.length" class="space-y-1.5 pt-2">
        <div class="text-p-sm font-medium text-ink-gray-6">
          {{ __('Dossiês gerados (PDF Executivo + JSON Auditável)') }}
        </div>
        <div
          v-for="group in groupedDossiers"
          :key="group.key"
          class="flex flex-wrap items-center justify-between gap-2 p-2.5 bg-surface-gray-1 rounded border border-outline-gray-1 text-p-sm"
        >
          <div class="flex items-center gap-2 min-w-0">
            <a
              v-if="group.pdf"
              :href="group.pdf.file_url"
              target="_blank"
              class="font-medium text-ink-blue-3 underline truncate"
            >
              {{ __('Abrir Dossiê Executivo (PDF)') }}
            </a>
            <span class="text-ink-gray-5">· {{ formatDate(group.creation) }}</span>
          </div>
          <a
            v-if="group.json"
            :href="group.json.file_url"
            target="_blank"
            class="text-p-xs text-ink-gray-6 hover:text-ink-gray-8 underline"
          >
            {{ __('JSON bruto (auditoria)') }}
          </a>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- PARECER EXECUTIVO DE CRÉDITO (IA) — 6 SEÇÕES SEMAFÓRICAS             -->
    <!-- ===================================================================== -->
    <div
      v-if="opinionStatus.data"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-3">
          <span class="text-lg-semibold text-ink-gray-9">{{
            __('Parecer Executivo de Crédito (IA · 6 Seções Semafóricas)')
          }}</span>
          <span v-if="opinionStatus.data" class="text-p-sm text-ink-gray-5">
            {{
              __('{0} de {1} pareceres usados neste mês', [
                opinionStatus.data.used,
                opinionStatus.data.included,
              ])
            }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button
            v-if="opinionStatus.data?.configured"
            :variant="hasNewerQueriesThanOpinion ? 'solid' : 'outline'"
            size="sm"
            :loading="requestingOpinion"
            @click="askOpinionOnly"
          >
            {{
              hasNewerQueriesThanOpinion
                ? __('Atualizar Parecer IA com Novos Dados')
                : __('Gerar / Reprocessar Parecer IA')
            }}
          </Button>
        </div>
      </div>

      <!-- Aviso quando entraram novas consultas avulsas após o último parecer -->
      <div
        v-if="hasNewerQueriesThanOpinion"
        class="p-3 rounded-lg border border-[#0088FF]/30 bg-[#E5F1FF] text-p-xs text-[#1E1F23] flex items-center justify-between gap-2"
      >
        <span>
          {{
            __(
              '💡 Novas consultas de bureau foram realizadas após a emissão do último parecer. Clique em "Atualizar Parecer IA com Novos Dados" para incorporar os novos retornos.',
            )
          }}
        </span>
      </div>

      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Parecer executivo direto ao ponto (1 a 2 páginas), estruturado em 6 seções fixas com semáforo de risco e citações verificadas dos bureaus. A decisão final é sempre do analista/comitê.',
          )
        }}
      </p>

      <div
        v-if="opinionStatus.data && !opinionStatus.data.configured"
        class="text-p-sm text-[color:var(--ct-warning)] font-medium"
      >
        {{ __('A IA de parecer de crédito ainda não está configurada neste ambiente.') }}
      </div>
      <div
        v-else-if="
          opinionStatus.data?.next_is_extra &&
          !opinionStatus.data?.extra_allowed
        "
        class="text-p-sm text-[color:var(--ct-warning)] font-medium"
      >
        {{
          __(
            'Os pareceres incluídos neste mês acabaram. Um administrador pode liberar pareceres extras pagos (R$ {0} cada) nas Configurações de Crédito.',
            [formatPrice(opinionStatus.data.extra_price)],
          )
        }}
      </div>

      <div v-if="opinions.data && opinions.data.length" class="space-y-4 pt-1">
        <div
          v-for="item in opinions.data"
          :key="item.name"
          class="p-4 border border-outline-gray-2 rounded-xl space-y-3 bg-[#F5F5F7]/40"
        >
          <div class="flex items-center justify-between gap-2 flex-wrap">
            <div class="flex items-center gap-2 flex-wrap">
              <Badge
                v-if="item.status === 'Done'"
                :theme="resultTheme(item.result)"
                variant="solid"
                size="lg"
                :label="resultLabel(item.result)"
              />
              <Badge
                v-else-if="item.status === 'Queued'"
                theme="blue"
                variant="subtle"
                :label="__('Gerando…')"
              />
              <Badge v-else theme="red" variant="subtle" :label="__('Falhou')" />
              <span class="text-p-sm text-ink-gray-5">
                {{ formatDate(item.requested_on) }} · {{ item.requested_by }}
              </span>
              <span v-if="item.is_extra" class="text-p-sm text-ink-gray-5">
                · {{ __('extra') }}
              </span>
            </div>
            <a
              v-if="item.pdf_url"
              :href="item.pdf_url"
              target="_blank"
              class="text-p-sm font-medium text-[#0088FF] underline"
            >
              {{ __('Abrir PDF do Parecer (PDF 2)') }}
            </a>
          </div>

          <!-- Renderização Estruturada em 6 Seções Semafóricas -->
          <template v-if="item.status === 'Done' && item.opinion">
            <div
              v-if="item.opinion.headline"
              class="text-base font-semibold text-[#1E1F23] bg-white p-3 rounded-lg border border-[#E6E7EB]"
            >
              {{ item.opinion.headline }}
            </div>

            <!-- Os Porquês (Summary Bullets) -->
            <div
              v-if="item.opinion.summary_bullets?.length"
              class="bg-white p-3.5 rounded-lg border border-[#E6E7EB] space-y-1.5"
            >
              <div class="text-xs font-bold uppercase tracking-wider text-[#5E6068]">
                {{ __('Principais Motivos da Recomendação (Os Porquês)') }}
              </div>
              <ul class="list-disc pl-5 space-y-1 text-p-sm text-[#1E1F23]">
                <li v-for="(bullet, bIdx) in item.opinion.summary_bullets" :key="bIdx">
                  {{ bullet }}
                </li>
              </ul>
            </div>

            <!-- Grid das 6 Seções Semafóricas -->
            <div
              v-if="item.opinion.sections?.length"
              class="grid grid-cols-1 md:grid-cols-2 gap-3"
            >
              <div
                v-for="sec in item.opinion.sections"
                :key="sec.key"
                class="p-3.5 bg-white rounded-lg border border-[#E6E7EB] space-y-2"
              >
                <div class="flex items-center justify-between gap-2">
                  <span class="text-p-sm font-semibold text-[#1E1F23]">
                    {{ sec.title }}
                  </span>
                  <Badge
                    :theme="sectionBadgeTheme(sec.status)"
                    variant="subtle"
                    :label="sectionBadgeLabel(sec.status)"
                  />
                </div>
                <ul
                  v-if="sec.findings?.length"
                  class="list-disc pl-4 space-y-1 text-p-xs text-[#2A2B30]"
                >
                  <li v-for="(f, fIdx) in sec.findings" :key="fIdx">
                    {{ f }}
                  </li>
                </ul>
                <div
                  v-if="sec.citations?.length"
                  class="flex flex-wrap gap-1 pt-1"
                >
                  <span
                    v-for="(cit, cIdx) in sec.citations"
                    :key="cIdx"
                    class="inline-block text-[11px] px-2 py-0.5 rounded bg-[#F5F5F7] text-[#5E6068] border border-[#E6E7EB]"
                  >
                    {{ cit.source }} · {{ cit.field }}: <strong>{{ cit.value }}</strong>
                  </span>
                </div>
              </div>
            </div>

            <!-- Condicionantes Sugeridas -->
            <div
              v-if="item.opinion.recommended_conditions?.length"
              class="bg-[#FFF4D6]/60 p-3.5 rounded-lg border border-[#8A5A00]/25 space-y-1"
            >
              <div class="text-xs font-bold uppercase tracking-wider text-[#8A5A00]">
                {{ __('Condicionantes & Garantias Recomendadas para o Comitê') }}
              </div>
              <ul class="list-disc pl-5 space-y-1 text-p-xs text-[#1E1F23]">
                <li
                  v-for="(cond, cIdx) in item.opinion.recommended_conditions"
                  :key="cIdx"
                >
                  {{ cond }}
                </li>
              </ul>
            </div>
          </template>

          <div v-else-if="item.status === 'Done'" class="text-p-sm text-ink-gray-7">
            {{ item.summary }}
          </div>
          <div v-if="item.status === 'Failed'" class="text-p-sm text-ink-red-3">
            {{ item.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Pasta Digital (Checklist de Documentos) e Relatório de Visita Técnica/Comercial -->
    <CreditOnboardingPanel
      :organization-id="props.organizationId"
      :deal-id="props.dealId"
    />

    <!-- ===================================================================== -->
    <!-- CONSULTAS AVULSAS NOS BUREAUS (SOB DEMANDA)                           -->
    <!-- ===================================================================== -->
    <div
      v-if="options.data && options.data.bureaus.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-4"
    >
      <div class="flex items-center justify-between">
        <span class="text-lg-semibold text-ink-gray-9">{{
          __('Consultas Avulsas nos Bureaus (Sob Demanda)')
        }}</span>
      </div>
      <p class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Cada consulta avulsa utiliza a conta da sua empresa no provedor. A CredTech não cobra taxa adicional.',
          )
        }}
      </p>
      <div
        v-if="options.data.needs_acknowledgement"
        class="p-3 rounded border border-outline-amber-2 bg-surface-amber-1 text-p-sm text-[color:var(--ct-warning)] font-medium space-y-1"
      >
        <div class="font-medium">
          {{ __('Triagem rápida: {0}', [verdictText(options.data.verdict)]) }}
        </div>
        <div v-if="options.data.verdict_summary">
          {{ options.data.verdict_summary }}
        </div>
        <div>
          {{
            __('Você ainda pode consultar normalmente (será solicitada confirmação do alerta).')
          }}
        </div>
      </div>
      <div class="grid grid-cols-1 gap-2">
        <div
          v-for="bureau in options.data.bureaus"
          :key="bureau.key"
          class="flex flex-wrap items-center justify-between p-3 border border-outline-gray-2 rounded gap-2"
        >
          <div class="space-y-0.5">
            <div class="flex items-center gap-2">
              <span class="text-base-medium">{{ bureau.label }}</span>
              <Badge
                :label="`Nível ${bureau.tier || 2}`"
                :theme="bureau.tier === 1 ? 'green' : bureau.tier === 3 ? 'amber' : 'blue'"
                variant="subtle"
              />
            </div>
            <div class="text-p-sm text-ink-gray-5">{{ priceText(bureau) }}</div>
            <div
              v-if="bureau.recent_company_query"
              class="text-p-xs text-ink-green-3 font-medium"
            >
              ✓ {{ __('Já consultado em {0} · Prazo para nova consulta: {1} dias (válido até {2})', [
                formatDate(bureau.recent_company_query.requested_on),
                bureau.recent_company_query.reuse_days,
                bureau.recent_company_query.valid_until,
              ]) }}
            </div>
            <div v-if="!bureau.configured" class="text-p-sm text-[color:var(--ct-warning)] font-medium">
              {{ __('Credencial/token ausente nas Configurações de Crédito.') }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Button
              v-if="bureau.partner_ok && selectedPartners.length"
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key + ':partners'"
              :disabled="!options.data.can_request || !bureau.configured"
              @click="askPremiumBureau(bureau, selectedPartners)"
            >
              {{ __('Consultar {0} sócio(s)', [selectedPartners.length]) }}
            </Button>
            <Button
              v-if="bureau.company_ok !== false"
              variant="outline"
              size="sm"
              :loading="requesting === bureau.key"
              :disabled="!options.data.can_request || !bureau.configured"
              @click="askPremiumBureau(bureau)"
            >
              {{ __('Consultar empresa') }}
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- HISTÓRICO DE CONSULTAS REALIZADAS (COM LEITURA FORMATADA HUMANA)     -->
    <!-- ===================================================================== -->
    <div
      v-if="results.data && results.data.length"
      class="p-5 bg-surface-white rounded-lg border border-outline-gray-2 space-y-3"
    >
      <span class="text-lg-semibold text-ink-gray-9">{{
        __('Histórico de Consultas Realizadas (Relatórios Formatados)')
      }}</span>
      <div
        v-for="row in results.data"
        :key="row.name"
        class="flex items-center justify-between p-3 border border-outline-gray-2 rounded gap-3"
      >
        <div class="min-w-0">
          <div class="text-base-medium">{{ row.bureau_label }}</div>
          <div class="text-p-sm text-ink-gray-6 truncate">
            {{ row.subject_name || __('Empresa') }} · {{ row.document }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ row.requested_on }} · {{ row.requested_by }}
          </div>
          <div
            v-if="row.warning_acknowledged"
            class="text-p-sm text-[color:var(--ct-warning)] font-medium"
          >
            {{
              __('Consultado com alerta de triagem: {0}', [
                verdictText(row.pre_filter_verdict),
              ])
            }}
          </div>
        </div>
        <Button variant="outline" size="sm" @click="openResult(row)">
          {{ __('Ver Relatório Formatado') }}
        </Button>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- MODAL DO RELATÓRIO DO BUREAU (VISÃO EXECUTIVA FORMATADA + TOGGLE JSON)-->
    <!-- ===================================================================== -->
    <Dialog v-model:open="showResult" :title="resultTitle" :size="'4xl'">
      <template #default>
        <div class="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-outline-gray-2">
          <p class="text-p-sm text-ink-gray-6">
            {{
              showRawJson
                ? __('JSON técnico bruto exatamente como retornado pela API do provedor (para fins de auditoria).')
                : __('Relatório formatado com todos os dados oficiais retornados pelo bureau.')
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
          >{{ resultText }}</pre
        >
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  Dialog,
  FormControl,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { createDialog } from '@/utils/dialogs'
import CreditOnboardingPanel from '@/components/CreditCheck/CreditOnboardingPanel.vue'

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

const recommendedTierBadge = computed(() => {
  const val = Number(requestedAmount.value || 0)
  if (!val || val <= 0) return null
  if (val <= 50000) {
    return {
      label: __('Recomendado: Nível 2 · Médio (R$ 10,89)'),
      theme: 'blue',
    }
  }
  return {
    label: __('Recomendado: Pular para Nível 3 · Profundo'),
    theme: 'amber',
  }
})

const org = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Organization',
    filters: props.organizationId,
    fieldname: ['credit_verdict', 'credit_report', 'cnpj'],
  },
  auto: true,
  transform: (d) => d?.message || d,
})

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

function reloadPackageStatus() {
  pkg.update({
    params: {
      organization_name: props.organizationId,
      deal_name: props.dealId || null,
      selected_contacts: JSON.stringify(selected.value),
      tier: selectedTierMode.value === 'default' ? null : selectedTierMode.value,
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

function verdictText(v) {
  if (!v || v === 'Not Checked') return __('Não verificado')
  if (v === 'Pre-Approved') return __('Pré-Aprovado')
  if (v === 'Warning') return __('Atenção')
  if (v === 'Rejected') return __('Reprovado')
  if (v === 'Error') return __('Provedores de triagem não configurados')
  return __(v)
}

const verdictLabel = computed(() => verdictText(org.data?.credit_verdict))

const verdictTheme = computed(() => {
  const v = org.data?.credit_verdict
  if (v === 'Rejected') return 'red'
  if (v === 'Warning') return 'amber'
  if (v === 'Pre-Approved') return 'green'
  return 'gray'
})

function sectionBadgeTheme(status) {
  if (status === 'clear') return 'green'
  if (status === 'attention') return 'amber'
  if (status === 'critical') return 'red'
  return 'gray'
}

function sectionBadgeLabel(status) {
  if (status === 'clear') return __('Regular')
  if (status === 'attention') return __('Atenção')
  if (status === 'critical') return __('Crítico')
  return __('Não Verificado')
}

function formatMoney(value) {
  return `R$ ${Number(value || 0)
    .toFixed(2)
    .replace('.', ',')}`
}

function priceText(bureau) {
  if (bureau.price_reference) {
    return __('Preço de tabela {0}, cobrado por {1} na sua conta', [
      formatMoney(bureau.price_reference),
      bureau.provider,
    ])
  }
  return __('Cobrado por {0} na sua conta, conforme seu contrato', [
    bureau.provider,
  ])
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
        { label: __('Cancelar (Manter Consulta Atual)'), variant: 'solid', onClick: ({ close }) => close() },
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
        __('Triagem Nível 1 enviada para execução. Atualize em instantes para ver o resultado.'),
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

// Detect if any bureau query was run AFTER the latest Done opinion
const hasNewerQueriesThanOpinion = computed(() => {
  const opList = opinions.data || []
  const qList = results.data || []
  if (!opList.length || !qList.length) return false
  const latestOp = opList.find((o) => o.status === 'Done')
  if (!latestOp || !latestOp.requested_on) return false
  const latestQueryOn = qList[0]?.requested_on
  return Boolean(latestQueryOn && String(latestQueryOn) > String(latestOp.requested_on))
})

let pollTimer = null
let pollRounds = 0

function resultLabel(result) {
  if (result === 'Approve') return __('Recomendação: Aprovar')
  if (result === 'Reject') return __('Recomendação: Reprovar')
  return __('Recomendação: Aprovar com ressalvas')
}

function resultTheme(result) {
  if (result === 'Approve') return 'green'
  if (result === 'Reject') return 'red'
  return 'amber'
}

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

function formatDate(value) {
  return value ? String(value).slice(0, 16) : ''
}

// Minimum package of the dossier (credtech#316)
const pkg = createResource({
  url: 'cred_hub.credit_check.api.get_dossier_package_status',
  params: {
    organization_name: props.organizationId,
    deal_name: props.dealId || null,
  },
  auto: true,
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
    return __('reaproveitado sem custo (consultado em {0})', [formatDate(entry.last_on)])
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
      byStamp[stampKey] = { key: stampKey, creation: file.creation, pdf: null, json: null }
      groups.push(byStamp[stampKey])
    }
    if (isPdf && !byStamp[stampKey].pdf) byStamp[stampKey].pdf = file
    if (isJson && !byStamp[stampKey].json) byStamp[stampKey].json = file
  }
  return groups.filter((g) => g.pdf || g.json)
})

async function askOpinionOnly() {
  const opinion = pkg.data?.opinion || opinionStatus.data || {}
  const extraOpinion = opinion.configured && opinion.next_is_extra && opinion.extra_allowed
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
    toast.error(err?.messages?.[0] || __('Não foi possível solicitar o parecer da IA.'))
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
      title: __('Consultas em dia (Prazo de {0} dias)', [data.reuse_days || 30]),
      message: __(
        'Todas as consultas selecionadas para esta empresa já foram realizadas recentemente. O prazo configurado para novas consultas na API do provedor é de {0} dias. Nenhuma nova consulta paga será disparada no provedor.',
        [data.reuse_days || 30],
      ),
      size: 'lg',
      actions: [
        { label: __('Cancelar'), onClick: ({ close }) => close() },
        {
          label: __('Apenas Gerar / Reprocessar Parecer IA'),
          variant: 'outline',
          onClick: ({ close }) => {
            close()
            triggerOpinionOnly(false)
          },
        },
        {
          label: __('Atualizar PDF do Dossiê (Sem Custo de API)'),
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
      __(
        'Consultas pagas, cobradas pelo provedor na sua conta: {0}.',
        [
          data.missing
            .map((entry) => `${entry.label} (${entry.subject_name})`)
            .join(', '),
        ],
      ),
    )
    lines.push(__('Cerca de {0} pelo preço de tabela.', [formatMoney(data.missing_cost)]))
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
        tier: selectedTierMode.value === 'default' ? null : selectedTierMode.value,
        requested_amount: requestedAmount.value || null,
      },
    )
    packageStarted.value = true
    if (res?.opinion_skipped) {
      toast.warning(
        __('Gerando dossiê sem o parecer da IA: {0}', [
          res.opinion_skipped,
        ]),
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
</script>
