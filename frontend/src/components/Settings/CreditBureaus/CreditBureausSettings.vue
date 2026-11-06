<template>
  <SettingsLayoutBase
    :title="__('Políticas de Crédito & Compliance')"
    :description="
      __('Regras de análise de crédito, prevenção a fraudes e consultas jurídicas.')
    "
  >
    <template #header-actions>
      <div v-if="settingsDoc" class="flex items-center gap-2">
        <Button
          variant="solid"
          :loading="saving"
          :disabled="!isAnyDirty"
          @click="saveAll"
        >
          {{ __('Salvar') }}
        </Button>
      </div>
    </template>

    <template #content>
      <div v-if="loading" class="flex items-center justify-center mt-[35%]">
        <LoadingIndicator class="size-6" />
      </div>
      <div
        v-else-if="settingsDoc"
        class="ct-credit space-y-6 pb-12 text-ink-gray-8"
      >
        <!-- Who pays (credtech#316): every paid query uses the client's own provider account -->
        <div
          class="flex gap-2.5 rounded-lg bg-[var(--ct-bg-soft)] px-4 py-3 text-p-base text-ink-gray-6"
        >
          <span class="lucide-info mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <span>
            {{
              __("Toda consulta paga usa a sua própria conta em cada provedor: o provedor cobra direto de você e a CredTech não cobra nada. Os preços mostrados são os preços de tabela dos provedores, só como referência; o seu contrato pode ser diferente.",
              )
            }}
          </span>
        </div>

        <!-- Quick section navigation pills so the page is clean and easy to present -->
        <div
          class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2 pb-3"
        >
          <button
            v-for="tab in sectionTabs"
            :key="tab.key"
            type="button"
            class="px-3.5 py-1.5 rounded-md text-p-sm font-medium transition-colors"
            :class="
              activeSection === tab.key
                ? 'bg-surface-gray-7 text-ink-white'
                : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'
            "
            @click="activeSection = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- ===================================================================== -->
        <!-- SECTION 1: FUNIS PRONTOS & PASTA DIGITAL DE DOCUMENTOS               -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'all' || activeSection === 'funnels'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('1. Modelos de Funil & Pasta Digital de Documentos') }}
            </span>
            <span class="text-base leading-5 text-ink-gray-6">
              {{
                __(
                  'Funis prontos para Securitizadoras, FIDCs, Factorings e Cobrança, além do checklist de documentos exigidos na análise.',
                )
              }}
            </span>
          </div>

          <!-- Funnel templates side by side -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <span class="text-lg-semibold text-ink-gray-9">{{
                  __('Funil Crédito PJ')
                }}</span>
                <Badge
                  :label="__('Originação & Crédito')"
                  theme="blue"
                  variant="subtle"
                />
              </div>
              <p class="text-p-xs text-ink-gray-6">
                {{
                  __('Um funil pronto para prospectar e analisar crédito de empresas (Securitizadoras, FIDCs, Factorings). Nada é obrigatório por etapa e não tem custo.',
                  )
                }}
              </p>
              <p
                v-if="template.data"
                class="text-p-sm font-medium text-ink-gray-9"
              >
                {{ template.data.stages.join(' → ') }}
              </p>
              <Button
                v-if="template.data && !template.data.installed"
                variant="outline"
                :loading="installing"
                @click="installTemplate"
              >
                {{ __('Instalar o funil Crédito PJ') }}
              </Button>
            </div>

            <div
              class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <span class="text-lg-semibold text-ink-gray-9">{{
                  __('Funil de Cobrança')
                }}</span>
                <Badge
                  :label="__('Recuperação & Cartório')"
                  theme="amber"
                  variant="subtle"
                />
              </div>
              <p class="text-p-xs text-ink-gray-6">
                {{
                  __('Envia títulos vencidos para protesto em cartório (CENPROT), localiza devedores e acompanha a recuperação todos os dias.',
                  )
                }}
              </p>
              <p
                v-if="collectionStatus.data?.stages"
                class="text-p-sm font-medium text-ink-gray-9"
              >
                {{ collectionStatus.data.stages.join(' → ') }}
              </p>
              <Button
                v-if="collectionStatus.data && !collectionStatus.data.installed"
                variant="outline"
                :loading="installingCollection"
                @click="installCollectionTemplate"
              >
                {{ __('Instalar o funil de Cobrança') }}
              </Button>
            </div>
          </div>

          <!-- Document Checklist Template Configuration -->
          <div
            class="space-y-4 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Checklist de Documentos da Pasta de Crédito') }}
                </span>
                <p class="text-p-xs text-ink-gray-6 mt-0.5">
                  {{
                    __(
                      'Defina quais documentos o cedente/cliente precisa entregar na análise (Contrato Social, RG/CNH dos Sócios, Faturamento, Endividamento, etc.). Em cada card ou organização você anexa os arquivos e dá o check de conferência.',
                    )
                  }}
                </p>
              </div>
              <Button variant="outline" size="sm" @click="addChecklistItem">
                + {{ __('Adicionar documento') }}
              </Button>
            </div>

            <div
              v-if="checklistItems.length"
              class="divide-y divide-outline-gray-1"
            >
              <div
                v-for="(docItem, idx) in checklistItems"
                :key="docItem.key || idx"
                class="py-2.5 flex flex-wrap items-center justify-between gap-3"
              >
                <div class="flex items-center gap-3 flex-1 min-w-[240px]">
                  <Checkbox v-model="docItem.enabled" />
                  <input
                    v-model="docItem.label"
                    type="text"
                    class="flex-1 rounded border border-outline-gray-2 px-3 py-1.5 text-p-sm text-ink-gray-9 bg-surface-white"
                    :placeholder="__('Nome do documento exigido')"
                  />
                </div>
                <div class="flex items-center gap-4">
                  <select
                    v-model="docItem.category"
                    class="rounded border border-outline-gray-2 px-2.5 py-1.5 text-p-sm text-ink-gray-8 bg-surface-white"
                  >
                    <option value="Societário">{{ __('Societário') }}</option>
                    <option value="Cadastral">{{ __('Cadastral') }}</option>
                    <option value="Financeiro">{{ __('Financeiro') }}</option>
                    <option value="Contábil">{{ __('Contábil') }}</option>
                    <option value="Operacional">{{ __('Operacional') }}</option>
                    <option value="Lastro">{{ __('Lastro / Títulos') }}</option>
                  </select>
                  <Checkbox
                    v-model="docItem.required"
                    :label="__('Obrigatório')"
                  />
                  <button
                    v-if="checklistItems.length > 1"
                    type="button"
                    class="text-ink-red-3 hover:text-ink-red-4 text-xs font-medium px-1"
                    :title="__('Remover item')"
                    @click="removeChecklistItem(idx)"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-2 pt-2">
              <Button
                variant="solid"
                :loading="savingChecklist"
                @click="saveChecklist"
              >
                {{ __('Salvar checklist de documentos') }}
              </Button>
            </div>
          </div>

          <!-- Stage Gate / Governance Locks -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div>
              <span class="text-lg-semibold text-ink-gray-9">
                {{ __('Travas de Governança no Funil (Stage Gate)') }}
              </span>
              <p class="text-p-xs text-ink-gray-6 mt-0.5">
                {{
                  __(
                    'Impeça que Cards avancem para Análise, Comitê ou Crédito Concedido sem os documentos obrigatórios da Pasta Digital ou sem o Dossiê de Crédito gerado.',
                  )
                }}
              </p>
            </div>
            <div class="space-y-2.5 pt-1">
              <Checkbox
                v-model="settingsDoc.enforce_checklist_on_stage_gate"
                :label="
                  __(
                    'Exigir todos os documentos obrigatórios anexados antes de avançar para Análise ou Comitê',
                  )
                "
              />
              <Checkbox
                v-if="settingsDoc.enforce_checklist_on_stage_gate"
                v-model="settingsDoc.require_verified_checklist_on_committee"
                :label="
                  __(
                    'Exigir check de Conferido (Verified) pela mesa de crédito antes de avançar para Comitê / Crédito Concedido',
                  )
                "
              />
              <Checkbox
                v-model="settingsDoc.enforce_dossier_on_committee"
                :label="
                  __(
                    'Exigir Dossiê / Relatório de Crédito gerado antes de avançar para Comitê / Crédito Concedido',
                  )
                "
              />
            </div>
          </div>
        </div>

        <SettingsDivider v-show="activeSection === 'all'" />

        <!-- ===================================================================== -->
        <!-- SECTION 2: BUREAUS DE CRÉDITO & CREDENCIAIS (SEMPRE VISÍVEIS)        -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'all' || activeSection === 'bureaus'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('2. Bureaus de Crédito & Credenciais de API') }}
            </span>
            <span class="text-base leading-5 text-ink-gray-6">
              {{
                __(
                  'Conecte suas contas nos provedores (DirectD, Serasa Experian, Escavador, Infosimples e CGU) para consultas de Dossiê e Pré-Filtro.',
                )
              }}
            </span>
          </div>

          <!-- 2.1 DirectD Unificado (Token + Relatórios de Dossiê + Pré-Filtro) -->
          <div
            class="space-y-4 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{
                    __(
                      'DirectD · Dossiê QUOD, SCR Bacen, Boa Vista, Score e Protestos',
                    )
                  }}
                </span>
                <Badge
                  :label="__('Principal · Dossiê & Pré-Filtro')"
                  theme="blue"
                  variant="subtle"
                />
              </div>
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Um único token DirectD habilita tanto os relatórios completos do dossiê (Dossiê QUOD, SCR Analítico do BACEN e Boa Vista) quanto as consultas rápidas do pré-filtro (Score QUOD, Protestos IEPTB Nacional, Processos, FGTS e Sintegra).',
                )
              }}
            </p>

            <!-- Token DirectD sempre acessível -->
            <div class="space-y-3 pt-1">
              <FormControl
                v-model="settingsDoc.directd_token"
                type="password"
                :label="__('Token da API DirectD')"
                :placeholder="__('Token da sua conta DirectD')"
                autocomplete="off"
              />
              <ProviderTest
                v-model="testCnpj.directd"
                :loading="testing === 'directd'"
                :disabled="!settingsDoc.directd_token"
                @test="
                  testProvider('directd', 'DirectD', settingsDoc.directd_token)
                "
              />
            </div>

            <!-- Sub-bloco A: Relatórios Completos para o Dossiê (Sob Demanda / Pacote Mínimo) -->
            <div class="pt-3 border-t border-outline-gray-2 space-y-2.5">
              <div class="text-p-sm font-semibold text-ink-gray-9">
                {{
                  __(
                    'Relatórios Completos para Dossiê (usados no Pacote Mínimo e consultas avulsas):',
                  )
                }}
              </div>
              <div
                v-for="bureau in directdBureaus"
                :key="bureau.field"
                class="flex items-center justify-between"
              >
                <Checkbox
                  v-model="settingsDoc[bureau.field]"
                  :label="bureau.label"
                />
                <span v-if="prices" class="text-p-sm text-ink-gray-6">
                  {{ __('Preço de tabela {0}', [formatMoney(prices[bureau.key])]) }}
                </span>
              </div>
            </div>

            <!-- Sub-bloco B: Consultas do Pré-Filtro Automático via DirectD -->
            <div class="pt-3 border-t border-outline-gray-2 space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-p-sm font-semibold text-ink-gray-9">
                    {{
                      __(
                        'Incluir DirectD no Pré-Filtro Rápido (Score QUOD + Protestos IEPTB + Processos)',
                      )
                    }}
                  </div>
                  <p v-if="prices" class="text-p-xs text-ink-gray-6">
                    {{
                      __('Preço de tabela por consulta: score {0}, protestos {1}, processos {2}; FGTS {3} e Sintegra {4} quando ligados. Cobrado pela DirectD na sua conta.',
                        [
                          formatMoney(prices.directd_score),
                          formatMoney(prices.directd_protestos),
                          formatMoney(prices.directd_processos),
                          formatMoney(prices.directd_fgts),
                          formatMoney(prices.directd_sintegra),
                        ],
                      )
                    }}
                  </p>
                </div>
                <Switch v-model="settingsDoc.directd_enabled" />
              </div>

              <div v-if="settingsDoc.directd_enabled" class="space-y-3 pt-1">
                <FormControl
                  v-model.number="settingsDoc.min_directd_score"
                  type="number"
                  :label="__('Score mínimo (0 = nunca reprovar por score)')"
                />
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  <Checkbox
                    v-model="settingsDoc.directd_fgts_enabled"
                    :label="__('Consultar regularidade do FGTS (CRF)')"
                  />
                  <Checkbox
                    v-model="settingsDoc.directd_sintegra_enabled"
                    :label="__('Consultar Sintegra / CCC (inscrição estadual)')"
                  />
                </div>
              </div>
            </div>

            <p
              v-if="usesDirectd && !settingsDoc.directd_token"
              class="text-p-sm text-[color:var(--ct-warning)] font-medium"
            >
              {{
                __(
                  'Informe o token da DirectD acima e clique em Salvar para usar os relatórios marcados.',
                )
              }}
            </p>
          </div>

          <!-- 2.2 Serasa Experian (Sempre visível) -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Serasa Experian · Relatório Avançado PJ') }}
                </span>
                <Badge
                  :label="__('Contrato Próprio')"
                  theme="amber"
                  variant="subtle"
                />
              </div>
              <Switch v-model="settingsDoc.serasa_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Habilita a consulta ao Relatório Avançado PJ PME diretamente no contrato Serasa Experian da sua empresa.',
                )
              }}
            </p>
            <div
              v-if="settingsDoc.serasa_enabled"
              class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2"
            >
              <FormControl
                v-model="settingsDoc.serasa_client_id"
                type="text"
                :label="__('Serasa Client ID')"
                autocomplete="off"
              />
              <FormControl
                v-model="settingsDoc.serasa_client_secret"
                type="password"
                :label="__('Serasa Client Secret')"
                autocomplete="off"
              />
              <FormControl
                v-model="settingsDoc.serasa_environment"
                type="select"
                :label="__('Ambiente Serasa')"
                :options="[
                  { label: __('Produção'), value: 'Production' },
                  {
                    label: __('Homologação (apenas testes)'),
                    value: 'Homologation',
                  },
                ]"
              />
              <FormControl
                v-model="settingsDoc.serasa_report_name"
                type="text"
                :label="__('Nome do relatório Serasa')"
              />
              <div class="md:col-span-2 flex items-center gap-3">
                <Button
                  variant="subtle"
                  :loading="testing === 'serasa'"
                  :disabled="!settingsDoc.serasa_client_id"
                  @click="testSerasa"
                >
                  {{ __('Testar login') }}
                </Button>
                <span class="text-p-sm text-ink-gray-5">
                  {{
                    __('Apenas valida o login na Serasa. Não faz consulta e não tem custo.',
                    )
                  }}
                </span>
              </div>
            </div>
          </div>

          <!-- 2.3 Escavador + Infosimples + CGU -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Escavador -->
            <div
              class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-lg-semibold text-ink-gray-9">
                    {{ __('Busca unificada de processos (Escavador)') }}
                  </span>
                  <Badge :label="__('Processos')" theme="blue" variant="subtle" />
                </div>
                <Switch v-model="settingsDoc.escavador_enabled" />
              </div>
              <p class="text-p-xs text-ink-gray-6">
                {{
                  __('Pesquisa processos cíveis, federais, trabalhistas e tribunais superiores (STJ/STF) em todo o Brasil pelo CNPJ.',
                  )
                }}
              </p>
              <p v-if="prices" class="text-p-xs text-ink-gray-6">
                {{
                  __('Preço de tabela: cerca de {0} por consulta, cobrado pelo Escavador na sua conta.',
                    [formatMoney(prices.escavador)],
                  )
                }}
              </p>
              <div v-if="settingsDoc.escavador_enabled" class="space-y-3 pt-2">
                <FormControl
                  v-model="settingsDoc.escavador_token"
                  type="password"
                  :label="__('Token da API Escavador')"
                  :placeholder="__('Token da sua conta Escavador')"
                  autocomplete="off"
                />
                <ProviderTest
                  v-model="testCnpj.escavador"
                  :loading="testing === 'escavador'"
                  :disabled="!settingsDoc.escavador_token"
                  @test="
                    testProvider(
                      'escavador',
                      'Escavador',
                      settingsDoc.escavador_token,
                    )
                  "
                />
              </div>
            </div>

            <!-- Infosimples -->
            <div
              class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-lg-semibold text-ink-gray-9">
                    {{
                      __('Regularidade fiscal e certidões federais (Infosimples)')
                    }}
                  </span>
                  <Badge :label="__('Fiscal')" theme="blue" variant="subtle" />
                </div>
                <Switch v-model="settingsDoc.infosimples_enabled" />
              </div>
              <p class="text-p-xs text-ink-gray-6">
                {{
                  __('Dívida Ativa da União (PGFN), CND Federal, CNDT Trabalhista e protestos em cartório.',
                  )
                }}
              </p>
              <p v-if="prices" class="text-p-xs text-ink-gray-6">
                {{
                  __('Preço de tabela: cerca de {0} por checagem (4 consultas), cobrado pela Infosimples na sua conta.',
                    [formatMoney(prices.infosimples)],
                  )
                }}
              </p>
              <div
                v-if="settingsDoc.infosimples_enabled"
                class="space-y-3 pt-2"
              >
                <FormControl
                  v-model="settingsDoc.infosimples_token"
                  type="password"
                  :label="__('Token da API Infosimples')"
                  :placeholder="__('Token da sua conta Infosimples')"
                  autocomplete="off"
                />
                <ProviderTest
                  v-model="testCnpj.infosimples"
                  :loading="testing === 'infosimples'"
                  :disabled="!settingsDoc.infosimples_token"
                  @test="
                    testProvider(
                      'infosimples',
                      'Infosimples',
                      settingsDoc.infosimples_token,
                    )
                  "
                />
              </div>
            </div>
          </div>

          <!-- 2.4 CGU CEIS/CNEP (Grátis) -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-lg-semibold text-ink-gray-9">
                  {{ __('Etapa 0: Sanções CEIS/CNEP (CGU)') }}
                </span>
                <Badge :label="__('Grátis')" theme="green" variant="subtle" />
              </div>
              <Switch v-model="settingsDoc.cgu_enabled" />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('Consulta inicial gratuita de sanções públicas (Portal da Transparência). Se a empresa estiver sancionada e o bloqueio estiver ativo, a análise já reprova na hora.',
                )
              }}
            </p>
            <div v-if="settingsDoc.cgu_enabled" class="pt-1">
              <Checkbox
                v-model="settingsDoc.block_on_ceis_cnep"
                :label="__('Reprovar imediatamente se constar no CEIS/CNEP')"
              />
            </div>
          </div>
        </div>

        <SettingsDivider v-show="activeSection === 'all'" />

        <!-- ===================================================================== -->
        <!-- SECTION 3: DOSSIÊ DE CRÉDITO & PARECER DA IA (METODOLOGIA 5 Cs)      -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'all' || activeSection === 'policy'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('3. Dossiê de Crédito & Parecer da IA') }}
            </span>
            <span class="text-base leading-5 text-ink-gray-6">
              {{
                __('O que a IA segue para escrever o parecer e as consultas que todo dossiê precisa ter.',
                )
              }}
            </span>
          </div>

          <!-- Minimum package of the credit dossier -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">{{
              __('Pacote mínimo do dossiê')
            }}</span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('As consultas que todo dossiê de crédito precisa ter. O botão "Gerar dossiê" mostra o que falta e o preço de tabela, faz as consultas que faltam com as suas chaves depois da confirmação e cria o PDF 1 e o parecer da IA. Só uma consulta deste pacote que falta ou falhou rebaixa a recomendação da IA.',
                )
              }}
            </p>
            <template v-if="packageDoc">
              <div class="text-base font-semibold text-ink-gray-9">
                {{ __('Empresa') }}
              </div>
              <div
                v-for="opt in packageOptions('company')"
                :key="opt.item"
                class="flex flex-wrap items-center gap-2"
              >
                <Checkbox
                  v-model="packageDoc.selected[opt.item]"
                  :label="packageOptionLabel(opt)"
                />
                <span
                  v-if="!isOptionConfigured(opt)"
                  class="text-p-sm text-[color:var(--ct-warning)] font-medium"
                >
                  {{
                    isOptionEnabled(opt)
                      ? __('falta informar o token/credencial na seção 2 acima')
                      : __('habilite este bureau na seção 2 acima')
                  }}
                </span>
              </div>
              <div class="pt-2 text-base font-semibold text-ink-gray-9">
                {{ __('Cada sócio com CPF completo') }}
              </div>
              <div
                v-for="opt in packageOptions('partners')"
                :key="opt.item"
                class="flex flex-wrap items-center gap-2"
              >
                <Checkbox
                  v-model="packageDoc.selected[opt.item]"
                  :label="packageOptionLabel(opt)"
                />
                <span
                  v-if="!isOptionConfigured(opt)"
                  class="text-p-sm text-[color:var(--ct-warning)] font-medium"
                >
                  {{
                    isOptionEnabled(opt)
                      ? __('falta informar o token/credencial na seção 2 acima')
                      : __('habilite este bureau na seção 2 acima')
                  }}
                </span>
              </div>
              <FormControl
                v-model.number="packageDoc.reuse_days"
                type="number"
                class="max-w-md"
                :label="
                  __('Reaproveitar consultas feitas há até quantos dias (0 = sempre consultar de novo)',
                  )
                "
              />
              <div class="text-base text-ink-gray-9">{{ packageCostText }}</div>
              <Button
                variant="solid"
                :loading="savingPackage"
                @click="savePackage"
              >
                {{ __('Salvar pacote') }}
              </Button>
            </template>
          </div>

          <!-- Credit policy the AI follows -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-lg-semibold text-ink-gray-9">{{
                __('Política de crédito (parecer da IA)')
              }}</span>
              <span v-if="policyDoc" class="text-xs text-ink-gray-6">
                {{
                  policyDoc.version
                    ? __('Versão {0}', [policyDoc.version])
                    : __('Política padrão')
                }}
              </span>
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('A IA escreve o parecer de crédito seguindo esta metodologia. Os parâmetros viram alertas automáticos no parecer; eles nunca reprovam sozinhos (0 = sem limite). Cada salvamento cria uma versão nova, e todo parecer guarda a versão que usou.',
                )
              }}
            </p>
            <template v-if="policyDoc">
              <FormControl
                v-model="policyDoc.methodology"
                type="textarea"
                :rows="14"
                :label="__('Metodologia')"
              />
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <FormControl
                    v-model.number="policyDoc.parameters.min_company_age_months"
                    type="number"
                    :label="__('Tempo mínimo de abertura da empresa (meses, 0 = sem limite)')"
                  />
                  <p class="mt-1 text-xs text-ink-gray-6">
                    {{
                      __(
                        'Empresas com menos tempo de abertura que isso geram alerta automático no parecer da IA. Ex: 12 = exige ao menos 1 ano de CNPJ. 0 = sem limite.',
                      )
                    }}
                  </p>
                </div>
                <div>
                  <FormControl
                    v-model.number="
                      policyDoc.parameters.max_scr_overdue_percent
                    "
                    type="number"
                    :label="
                      __('Tolerância de dívida bancária vencida no SCR (%)')
                    "
                  />
                  <p class="mt-1 text-xs text-ink-gray-6">
                    {{
                      __(
                        'Percentual máximo aceitável de dívida bancária vencida no Banco Central (SCR). Ex: 10 significa que se mais de 10% da dívida total nos bancos estiver em atraso, a IA destaca alerta de risco no parecer. 0 = sem limite.',
                      )
                    }}
                  </p>
                </div>
              </div>
              <Checkbox
                v-model="policyDoc.parameters.alert_partner_restrictions"
                :label="__('Alertar quando um sócio tiver restrições')"
              />
              <div class="pt-3 mt-2 border-t border-outline-gray-2 space-y-1">
                <Checkbox
                  v-model="settingsDoc.allow_paid_extra_opinions"
                  :label="__('Permitir pareceres extras pagos')"
                />
                <p class="pl-6 text-p-xs text-ink-gray-6">
                  {{
                    __('Cada empresa tem 30 pareceres da IA por mês incluídos. Com isto ligado, a partir do 31º cada parecer custa R$ 3,00 da carteira de créditos, com confirmação antes. Desligado, o parecer para até o mês seguinte.',
                    )
                  }}
                </p>
              </div>
              <div class="flex items-center gap-2 pt-2">
                <Button
                  variant="solid"
                  :loading="savingPolicy"
                  @click="savePolicy"
                >
                  {{ __('Salvar política') }}
                </Button>
                <Button variant="subtle" @click="restoreDefaultPolicy">
                  {{ __('Voltar ao texto padrão') }}
                </Button>
              </div>
            </template>
          </div>
        </div>

        <SettingsDivider v-show="activeSection === 'all'" />

        <!-- ===================================================================== -->
        <!-- SECTION 4: ESTEIRA AUTOMÁTICA DE PRÉ-FILTRO & RÉGUA DE CORTE         -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'all' || activeSection === 'prefilter'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span class="text-lg font-semibold leading-6 text-ink-gray-9">
              {{ __('4. Esteira Automática de Pré-Filtro & Régua de Corte') }}
            </span>
            <span class="text-base leading-5 text-ink-gray-6">
              {{
                __(
                  'Defina quando a triagem rápida roda sozinha no funil e quais limites disparam alerta ou bloqueio imediato.',
                )
              }}
            </span>
          </div>

          <!-- Master Enable Switch -->
          <div
            class="flex items-center justify-between gap-4 rounded-lg bg-[var(--ct-bg-soft)] px-5 py-4"
          >
            <div class="flex flex-col gap-1">
              <span class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('Habilitar esteira de risco e compliance') }}
              </span>
              <span class="text-base text-ink-gray-6">
                {{
                  __('Triagem automática de sanções, processos judiciais, dívida ativa federal, certidões e protestos em cartório.',
                  )
                }}
              </span>
            </div>
            <Switch v-model="settingsDoc.enabled" />
          </div>

          <!-- Funnel automation trigger -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Gatilho automático no funil') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('Executa a triagem automaticamente quando um card entra nesta etapa. Cada triagem automática consome consultas nos provedores habilitados.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormControl
                v-model="settingsDoc.auto_trigger_stage"
                type="text"
                :label="__('Nome da etapa que dispara a triagem')"
                placeholder="ex: Consultas"
              />
              <div class="flex items-center gap-2 pt-6">
                <Checkbox
                  v-model="settingsDoc.check_second_organization"
                  :label="
                    __('Também consultar a segunda organização (sacado), se houver')
                  "
                />
              </div>
            </div>
          </div>

          <!-- Risk tolerance and blocks -->
          <div
            class="space-y-3 rounded-lg border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-lg-semibold text-ink-gray-9">
              {{ __('Critérios de risco e bloqueios automáticos') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('Nada reprova sozinho por padrão: o sistema gera alerta e o analista decide. Ligue um bloqueio ou defina limite acima de 0 apenas se sua política reprovar automaticamente.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model.number="settingsDoc.max_lawsuits_defendant"
                type="number"
                :label="
                  __('Máximo de processos como réu (0 = sem limite, apenas alerta)')
                "
              />
              <FormControl
                v-model.number="settingsDoc.max_pgfn_debt"
                type="number"
                :label="
                  __('Dívida máxima tolerada na PGFN (R$) (0 = sem limite, apenas alerta)',
                  )
                "
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="
                  __('Reprovar imediatamente em caso de recuperação judicial ou falência')
                "
              />
              <Checkbox
                v-model="settingsDoc.block_on_protest"
                :label="__('Reprovar imediatamente se houver protesto em cartório')"
              />
              <Checkbox
                v-if="settingsDoc.directd_fgts_enabled"
                v-model="settingsDoc.block_on_fgts_irregular"
                :label="__('Reprovar se o FGTS estiver irregular')"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import {
  Button,
  FormControl,
  Checkbox,
  Switch,
  Badge,
  LoadingIndicator,
  toast,
  call,
  createResource,
} from 'frappe-ui'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsDivider from '@/components/Settings/SettingsDivider.vue'
import { createDialog } from '@/utils/dialogs'

// Small inline control: CNPJ for the test + "Test connection" button.
const ProviderTest = {
  props: { modelValue: String, loading: Boolean, disabled: Boolean },
  emits: ['update:modelValue', 'test'],
  setup(props, { emit }) {
    return () =>
      h('div', { class: 'flex items-center gap-2' }, [
        h(FormControl, {
          type: 'text',
          class: 'w-48',
          placeholder: __('CNPJ para teste'),
          modelValue: props.modelValue,
          'onUpdate:modelValue': (value) => emit('update:modelValue', value),
        }),
        h(
          Button,
          {
            variant: 'subtle',
            loading: props.loading,
            disabled: props.disabled || !props.modelValue,
            onClick: () => emit('test'),
          },
          () => __('Testar conexão'),
        ),
      ])
  },
}

const activeSection = ref('all')
const sectionTabs = computed(() => [
  { key: 'all', label: __('Visão Geral (Tudo)') },
  { key: 'funnels', label: __('1. Funis & Documentos') },
  { key: 'bureaus', label: __('2. Bureaus & Credenciais') },
  { key: 'policy', label: __('3. Dossiê & Parecer IA') },
  { key: 'prefilter', label: __('4. Pré-Filtro & Régua') },
])

const loading = ref(true)
const saving = ref(false)
const testing = ref('')
const originalDoc = ref(null)

const settingsDoc = ref({
  enabled: false,
  cgu_enabled: false,
  block_on_ceis_cnep: false,
  escavador_enabled: false,
  escavador_token: '',
  infosimples_enabled: false,
  infosimples_token: '',
  directd_enabled: false,
  directd_token: '',
  min_directd_score: 0,
  directd_fgts_enabled: false,
  directd_sintegra_enabled: false,
  auto_trigger_stage: '',
  check_second_organization: true,
  max_lawsuits_defendant: 0,
  max_lawsuit_value: 0,
  block_on_bankruptcy: false,
  max_pgfn_debt: 0,
  block_on_cndt: false,
  block_on_protest: false,
  block_on_fgts_irregular: false,
  serasa_enabled: false,
  serasa_client_id: '',
  serasa_client_secret: '',
  serasa_environment: 'Production',
  serasa_report_name: 'RELATORIO_AVANCADO_PJ_PME',
  boavista_risco_enabled: false,
  dossie_quod_enabled: false,
  scr_bacen_enabled: false,
  allow_paid_extra_opinions: false,
  enforce_checklist_on_stage_gate: false,
  require_verified_checklist_on_committee: false,
  enforce_dossier_on_committee: false,
})

const directdBureaus = [
  {
    key: 'dossie_quod',
    field: 'dossie_quod_enabled',
    label: 'Dossiê QUOD - Completo',
  },
  {
    key: 'scr_bacen',
    field: 'scr_bacen_enabled',
    label: 'SCR Analítico - Resumo BACEN',
  },
  {
    key: 'boavista_risco',
    field: 'boavista_risco_enabled',
    label: 'Boa Vista - Risco Positivo PJ',
  },
]

// Live reactivity for Minimum Package warnings when user toggles bureaus or enters tokens above
function isOptionEnabled(opt) {
  if (opt.bureau === 'serasa') return Boolean(settingsDoc.value.serasa_enabled)
  if (opt.bureau === 'dossie_quod')
    return Boolean(settingsDoc.value.dossie_quod_enabled)
  if (opt.bureau === 'scr_bacen')
    return Boolean(settingsDoc.value.scr_bacen_enabled)
  if (opt.bureau === 'boavista_risco')
    return Boolean(settingsDoc.value.boavista_risco_enabled)
  return Boolean(opt.enabled)
}

function isOptionConfigured(opt) {
  if (!isOptionEnabled(opt)) return false
  if (opt.bureau === 'serasa') {
    return Boolean(
      settingsDoc.value.serasa_client_id &&
        settingsDoc.value.serasa_client_secret,
    )
  }
  return Boolean(settingsDoc.value.directd_token)
}

// Document Checklist Template
const checklistItems = ref([])
const originalChecklistJson = ref('')
const savingChecklist = ref(false)

async function loadChecklist() {
  try {
    const res = await call('cred_hub.credit_check.api.get_checklist_template')
    checklistItems.value = Array.isArray(res?.items) ? res.items : []
    originalChecklistJson.value = JSON.stringify(checklistItems.value)
  } catch {
    checklistItems.value = []
  }
}

function addChecklistItem() {
  checklistItems.value.push({
    key: `doc_${Date.now()}`,
    label: '',
    category: 'Financeiro',
    required: false,
    enabled: true,
  })
}

function removeChecklistItem(index) {
  checklistItems.value.splice(index, 1)
}

async function saveChecklist() {
  savingChecklist.value = true
  try {
    const res = await call(
      'cred_hub.credit_check.api.save_checklist_template',
      {
        items: JSON.stringify(checklistItems.value),
      },
    )
    checklistItems.value = res.items || checklistItems.value
    originalChecklistJson.value = JSON.stringify(checklistItems.value)
    toast.success(__('Checklist de documentos salvo com sucesso!'))
  } catch (err) {
    toast.error(
      err?.messages?.[0] || __('Não foi possível salvar o checklist.'),
    )
  } finally {
    savingChecklist.value = false
  }
}

const policyDoc = ref(null)
const originalPolicyJson = ref('')
const savingPolicy = ref(false)
let defaultMethodology = ''

async function loadPolicy() {
  try {
    const res = await call('cred_hub.credit_check.api.get_credit_policy')
    defaultMethodology = res.default_methodology
    policyDoc.value = {
      version: res.version,
      methodology: res.methodology,
      parameters: {
        ...res.parameters,
        alert_partner_restrictions: Boolean(
          res.parameters.alert_partner_restrictions,
        ),
      },
    }
    originalPolicyJson.value = JSON.stringify({
      methodology: policyDoc.value.methodology,
      parameters: policyDoc.value.parameters,
    })
  } catch {
    policyDoc.value = null
  }
}

async function savePolicy() {
  savingPolicy.value = true
  try {
    const res = await call('cred_hub.credit_check.api.save_credit_policy', {
      methodology: policyDoc.value.methodology,
      parameters: JSON.stringify({
        ...policyDoc.value.parameters,
        alert_partner_restrictions: policyDoc.value.parameters
          .alert_partner_restrictions
          ? 1
          : 0,
      }),
    })
    policyDoc.value.version = res.version
    originalPolicyJson.value = JSON.stringify({
      methodology: policyDoc.value.methodology,
      parameters: policyDoc.value.parameters,
    })
    // Also persist allow_paid_extra_opinions so the user doesn't have to click two Save buttons
    await call('frappe.client.set_value', {
      doctype: 'Cred Hub Credit Settings',
      name: 'Cred Hub Credit Settings',
      fieldname: {
        allow_paid_extra_opinions: settingsDoc.value.allow_paid_extra_opinions
          ? 1
          : 0,
      },
    })
    if (originalDoc.value) {
      originalDoc.value.allow_paid_extra_opinions =
        settingsDoc.value.allow_paid_extra_opinions
    }
    toast.success(__('Política de crédito salva (versão {0}).', [res.version]))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível salvar a política de crédito.'))
  } finally {
    savingPolicy.value = false
  }
}

function restoreDefaultPolicy() {
  if (policyDoc.value && defaultMethodology) {
    policyDoc.value.methodology = defaultMethodology
  }
}

// Minimum package of the dossier (credtech#316): default Dossiê QUOD + SCR Bacen of the company, 30 days of reuse
const packageDoc = ref(null)
const originalPackageJson = ref('')
const savingPackage = ref(false)

async function loadPackage() {
  try {
    const res = await call('cred_hub.credit_check.api.get_dossier_package')
    const selected = {}
    for (const opt of res.options)
      selected[opt.item] = res.items.includes(opt.item)
    packageDoc.value = {
      options: res.options,
      selected,
      reuse_days: res.reuse_days,
    }
    originalPackageJson.value = JSON.stringify({
      selected: packageDoc.value.selected,
      reuse_days: packageDoc.value.reuse_days,
    })
  } catch {
    packageDoc.value = null
  }
}

function packageOptions(scope) {
  return (packageDoc.value?.options || []).filter((opt) => opt.scope === scope)
}

function packageOptionLabel(opt) {
  return opt.price_reference
    ? `${opt.label} — ${formatMoney(opt.price_reference)}`
    : `${opt.label} — ${__('conforme o seu contrato')}`
}

const packageCostText = computed(() => {
  if (!packageDoc.value) return ''
  const chosen = packageDoc.value.options.filter(
    (opt) => packageDoc.value.selected[opt.item],
  )
  const sum = (scope) =>
    chosen
      .filter((opt) => opt.scope === scope)
      .reduce((total, opt) => total + (opt.price_reference || 0), 0)
  let text = __('Cerca de {0} por empresa pelo preço de tabela, cobrado pelo provedor na sua conta.',
    [formatMoney(sum('company'))],
  )
  if (sum('partners'))
    text +=
      ' ' +
      __('Mais {0} por cada sócio com CPF.', [
        formatMoney(sum('partners')),
      ])
  if (chosen.some((opt) => !opt.price_reference))
    text += ' ' + __('A Serasa é cobrada conforme o seu contrato.')
  return text
})

async function savePackage() {
  savingPackage.value = true
  try {
    const items = Object.keys(packageDoc.value.selected).filter(
      (item) => packageDoc.value.selected[item],
    )
    const res = await call('cred_hub.credit_check.api.save_dossier_package', {
      items: JSON.stringify(items),
      reuse_days: packageDoc.value.reuse_days,
    })
    packageDoc.value.reuse_days = res.reuse_days
    originalPackageJson.value = JSON.stringify({
      selected: packageDoc.value.selected,
      reuse_days: packageDoc.value.reuse_days,
    })
    toast.success(__('Pacote mínimo salvo com sucesso!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível salvar o pacote mínimo.'))
  } finally {
    savingPackage.value = false
  }
}

const template = createResource({
  url: 'cred_hub.credit_check.api.get_credit_template_status',
  auto: true,
})
const installing = ref(false)

const collectionStatus = createResource({
  url: 'cred_hub.integrations.protest.collection_funnel_status',
  auto: true,
})

const installingCollection = ref(false)

async function installTemplate() {
  installing.value = true
  try {
    await call('cred_hub.credit_check.api.install_credit_template')
    template.reload()
    toast.success(__('Funil Crédito PJ instalado com sucesso!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível instalar o funil.'))
  } finally {
    installing.value = false
  }
}

async function installCollectionTemplate() {
  installingCollection.value = true
  try {
    const res = await call(
      'cred_hub.integrations.protest.install_collection_template',
    )
    collectionStatus.reload()
    toast.success(__('Debt Collection funnel installed: {0}.', [res.pipeline]))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Não foi possível instalar o funil.'))
  } finally {
    installingCollection.value = false
  }
}

const testCnpj = ref({ escavador: '', infosimples: '', directd: '' })

const usesDirectd = computed(
  () =>
    settingsDoc.value.directd_enabled ||
    directdBureaus.some((bureau) => settingsDoc.value[bureau.field]),
)

const isDirty = computed(() => {
  if (!originalDoc.value) return false
  return JSON.stringify(settingsDoc.value) !== JSON.stringify(originalDoc.value)
})

const isChecklistDirty = computed(() => {
  if (!originalChecklistJson.value) return false
  return JSON.stringify(checklistItems.value) !== originalChecklistJson.value
})

const isPolicyDirty = computed(() => {
  if (!policyDoc.value || !originalPolicyJson.value) return false
  return (
    JSON.stringify({
      methodology: policyDoc.value.methodology,
      parameters: policyDoc.value.parameters,
    }) !== originalPolicyJson.value
  )
})

const isPackageDirty = computed(() => {
  if (!packageDoc.value || !originalPackageJson.value) return false
  return (
    JSON.stringify({
      selected: packageDoc.value.selected,
      reuse_days: packageDoc.value.reuse_days,
    }) !== originalPackageJson.value
  )
})

const isAnyDirty = computed(
  () =>
    isDirty.value ||
    isChecklistDirty.value ||
    isPolicyDirty.value ||
    isPackageDirty.value,
)

const priceResource = createResource({
  url: 'cred_hub.credit_check.api.get_price_references',
  auto: true,
})
const prices = computed(() => priceResource.data || null)

function formatMoney(value) {
  return `R$ ${Number(value || 0)
    .toFixed(2)
    .replace('.', ',')}`
}

async function loadSettings() {
  loading.value = true
  try {
    const res = await createResource({
      url: 'frappe.client.get',
      params: { doctype: 'Cred Hub Credit Settings' },
    }).fetch()
    if (res) {
      for (const key of Object.keys(settingsDoc.value)) {
        if (key in res) {
          settingsDoc.value[key] = res[key]
        }
      }
      originalDoc.value = JSON.parse(JSON.stringify(settingsDoc.value))
    }
  } catch {
    // If not exists, keep defaults
  } finally {
    loading.value = false
  }
}

async function saveAll() {
  saving.value = true
  try {
    if (isDirty.value) {
      const cleanFields = { ...settingsDoc.value }
      for (const metaKey of [
        'doctype',
        'name',
        'modified',
        'creation',
        'owner',
        'modified_by',
        'docstatus',
        'idx',
      ]) {
        delete cleanFields[metaKey]
      }
      await call('frappe.client.set_value', {
        doctype: 'Cred Hub Credit Settings',
        name: 'Cred Hub Credit Settings',
        fieldname: cleanFields,
      })
      originalDoc.value = JSON.parse(JSON.stringify(settingsDoc.value))
    }
    if (isChecklistDirty.value) {
      await saveChecklist()
    }
    if (isPackageDirty.value) {
      await savePackage()
    }
    if (isPolicyDirty.value) {
      await savePolicy()
    }
    await loadPackage()
    toast.success(__('Configurações de crédito salvas com sucesso!'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Falha ao salvar as configurações de crédito.'))
  } finally {
    saving.value = false
  }
}

function testProvider(provider, label, token) {
  const cnpj = testCnpj.value[provider]
  if (!token || !cnpj) return
  const cost = prices.value?.test_connection?.[provider]
  createDialog({
    title: __('Testar conexão'),
    message: __('O teste executa uma consulta real no CNPJ {0}, cobrada por {1} na sua conta (preço de tabela cerca de {2}). A CredTech não cobra nada.',
      [cnpj, label, formatMoney(cost)],
    ),
    size: 'md',
    actions: [
      {
        label: __('Cancelar'),
        onClick: ({ close }) => close(),
      },
      {
        label: __('Executar teste pago'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          runTest(provider, token, cnpj)
        },
      },
    ],
  })
}

async function testSerasa() {
  testing.value = 'serasa'
  try {
    const res = await call('cred_hub.credit_check.api.test_serasa_connection', {
      client_id: settingsDoc.value.serasa_client_id,
      client_secret: settingsDoc.value.serasa_client_secret,
      environment: settingsDoc.value.serasa_environment,
    })
    if (res?.ok) {
      toast.success(res.message || __('Conexão realizada com sucesso!'))
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Falha na conexão.'))
  } finally {
    testing.value = ''
  }
}

async function runTest(provider, token, cnpj) {
  testing.value = provider
  try {
    const res = await call(
      'cred_hub.credit_check.api.test_provider_connection',
      {
        provider,
        token,
        cnpj,
        confirm_cost: 1,
      },
    )
    if (res?.ok) {
      toast.success(res.message || __('Conexão realizada com sucesso!'))
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Falha na conexão.'))
  } finally {
    testing.value = ''
  }
}

onMounted(() => {
  loadSettings()
  loadPolicy()
  loadPackage()
  loadChecklist()
})
</script>

<style scoped>
/* Figma "Campo": 48px fields, labels 14/500 gray */
.ct-credit :deep(input:not([type='checkbox']):not([type='radio'])),
.ct-credit :deep(select) {
  height: 48px;
  background-color: var(--ct-bg-page);
  border-color: var(--ct-border);
  font-size: 16px;
  padding-inline: 14px;
  border-radius: 6px;
}
.ct-credit :deep(textarea) {
  background-color: var(--ct-bg-page);
  border-color: var(--ct-border);
  font-size: 16px;
  padding: 12px 14px;
  border-radius: 6px;
}
.ct-credit :deep(label.block) {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-gray-6);
}
</style>
