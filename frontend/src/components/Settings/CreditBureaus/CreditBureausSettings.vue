<template>
  <!-- Figma "Configurações · Políticas de Crédito & Compliance" (1999:53488 …):
       title "Crédito e Compliance", blue info notice, 4 underlined tabs -->
  <SettingsLayoutBase :title="__('Crédito e Compliance')">
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
        class="ct-credit flex flex-col gap-6 pb-12 text-ink-gray-8"
      >
        <!-- Who pays (credtech#316): every paid query uses the client's own provider account.
             Figma "Aviso (toast)" · Informação -->
        <div
          class="flex min-h-11 items-center gap-2.5 rounded-[var(--ct-radius-md)] bg-[var(--ct-accent-soft)] py-2.5 pl-3.5 pr-2.5"
        >
          <span
            class="lucide-info size-5 shrink-0 text-[var(--ct-accent)]"
            aria-hidden="true"
          />
          <span
            class="flex-1 text-[14px] font-medium leading-5 text-[var(--ct-accent)]"
          >
            {{
              __("Toda consulta paga usa a sua própria conta em cada provedor: o provedor cobra direto de você e a CredTech não cobra nada. Os preços mostrados são os preços de tabela dos provedores, só como referência; o seu contrato pode ser diferente.",
              )
            }}
          </span>
        </div>

        <!-- Figma "Aba": 14 Medium, 4px/10px padding, 2px blue line on the active tab -->
        <div
          class="flex items-start gap-4 border-b border-[var(--ct-border)]"
          role="tablist"
        >
          <button
            v-for="tab in sectionTabs"
            :key="tab.key"
            type="button"
            role="tab"
            :aria-selected="activeSection === tab.key"
            class="flex flex-col"
            @click="activeSection = tab.key"
          >
            <span
              class="px-1 py-2.5 text-[14px] font-medium leading-5"
              :class="
                activeSection === tab.key
                  ? 'text-[var(--ct-accent)]'
                  : 'text-[var(--ct-text-secondary)] hover:text-[var(--ct-text-primary)]'
              "
            >
              {{ tab.label }}
            </span>
            <span
              class="h-0.5 w-full"
              :class="activeSection === tab.key ? 'bg-[var(--ct-accent)]' : ''"
            />
          </button>
        </div>

        <!-- ===================================================================== -->
        <!-- TAB 1: FUNIS E DOCUMENTOS (Figma 1999:53539)                          -->
        <!-- ===================================================================== -->
        <div v-show="activeSection === 'funnels'" class="flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <span
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Modelos de Funil & Pasta Digital de Documentos') }}
            </span>
            <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
              {{
                __(
                  'Funis prontos para Securitizadoras, FIDCs, Factorings e Cobrança, além do checklist de documentos exigidos na análise.',
                )
              }}
            </span>
          </div>

          <!-- Funnel templates: one bordered list, one row per funnel -->
          <div
            class="flex flex-col overflow-hidden rounded-[var(--ct-radius-md)] border border-[var(--ct-border)]"
          >
            <div
              class="flex items-center gap-4 border-b border-[var(--ct-border)] px-4 py-3.5"
            >
              <div class="flex min-w-0 flex-1 flex-col gap-1">
                <div class="flex items-center gap-2">
                  <span
                    class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
                  >
                    {{ __('Funil Crédito PJ') }}
                  </span>
                  <span
                    class="rounded-full bg-[var(--ct-accent-soft)] px-2.5 py-0.5 text-[12px] font-medium leading-4 text-[var(--ct-accent)]"
                  >
                    {{ __('Originação & Crédito') }}
                  </span>
                </div>
                <p
                  class="text-[12px] leading-4 text-[var(--ct-text-secondary)]"
                >
                  {{
                    __(
                      'Um funil pronto para prospectar e analisar crédito de empresas. É só um ponto de partida: você edita etapas, campos e regras como em qualquer funil. Nada é obrigatório por etapa e não tem custo.',
                    )
                  }}
                </p>
              </div>
              <span
                v-if="template.data?.installed"
                class="flex shrink-0 items-center gap-1.5 rounded-full bg-[var(--ct-success-soft)] px-2.5 py-0.5 text-[12px] font-medium leading-4 text-[var(--ct-success)]"
              >
                <span class="size-1.5 rounded-full bg-[var(--ct-success)]" />
                {{ __('Instalado') }}
              </span>
              <Button
                v-else-if="template.data"
                variant="outline"
                size="md"
                :loading="installing"
                @click="installTemplate"
              >
                {{ __('Instalar o funil Crédito PJ') }}
              </Button>
            </div>

            <div class="flex items-center gap-4 px-4 py-3.5">
              <div class="flex min-w-0 flex-1 flex-col gap-1">
                <div class="flex items-center gap-2">
                  <span
                    class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
                  >
                    {{ __('Funil de Cobrança') }}
                  </span>
                  <span
                    class="rounded-full bg-[var(--ct-bg-panel)] px-2.5 py-0.5 text-[12px] font-medium leading-4 text-[var(--ct-text-primary)]"
                  >
                    {{ __('Recuperação & Cartório') }}
                  </span>
                </div>
                <p
                  class="text-[12px] leading-4 text-[var(--ct-text-secondary)]"
                >
                  {{
                    __(
                      'Um funil pronto para recuperar títulos vencidos, negociar acordos e enviar a protesto em cartório.',
                    )
                  }}
                </p>
              </div>
              <span
                v-if="collectionStatus.data?.installed"
                class="flex shrink-0 items-center gap-1.5 rounded-full bg-[var(--ct-success-soft)] px-2.5 py-0.5 text-[12px] font-medium leading-4 text-[var(--ct-success)]"
              >
                <span class="size-1.5 rounded-full bg-[var(--ct-success)]" />
                {{ __('Instalado') }}
              </span>
              <Button
                v-else-if="collectionStatus.data"
                variant="outline"
                size="md"
                :loading="installingCollection"
                @click="installCollectionTemplate"
              >
                {{ __('Instalar o funil de Cobrança') }}
              </Button>
            </div>
          </div>

          <!-- Document checklist (Figma 2001:3796) -->
          <div
            class="flex flex-col gap-4 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-start gap-4">
              <div class="flex min-w-0 flex-1 flex-col gap-0.5">
                <span
                  class="text-[16px] font-semibold leading-[23px] text-[var(--ct-text-primary)]"
                >
                  {{ __('Checklist de Documentos da Pasta de Crédito') }}
                </span>
                <p
                  class="max-w-[820px] text-[13px] leading-[19px] text-[var(--ct-text-secondary)]"
                >
                  {{
                    __(
                      'Defina quais documentos o cedente/cliente precisa entregar na análise (Contrato Social, RG/CNH dos Sócios, Faturamento, Endividamento, etc.). Em cada card ou organização você anexa os arquivos e dá o check de conferência.',
                    )
                  }}
                </p>
              </div>
              <Button
                variant="outline"
                size="md"
                class="ct-btn-accent-text shrink-0"
                @click="addChecklistItem"
              >
                + {{ __('Adicionar documento') }}
              </Button>
            </div>

            <div
              v-for="(docItem, idx) in checklistItems"
              :key="docItem.key || idx"
              class="flex items-center justify-between gap-4"
            >
              <div class="flex min-w-0 items-center gap-4">
                <Checkbox v-model="docItem.enabled" />
                <input
                  v-model="docItem.label"
                  type="text"
                  class="w-[520px] min-w-0 shrink text-[var(--ct-text-primary)]"
                  :placeholder="__('Nome do documento exigido')"
                />
                <select
                  v-model="docItem.category"
                  class="w-[200px] shrink-0 text-[var(--ct-text-primary)]"
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
                  class="shrink-0"
                  :label="__('Obrigatório')"
                />
              </div>
              <!-- Style Guide: trash always red (Paleta/Feedback/Erro) -->
              <button
                v-if="checklistItems.length > 1"
                type="button"
                class="flex size-8 shrink-0 items-center justify-center rounded-[var(--ct-radius-sm)] text-[var(--ct-danger)] hover:bg-[var(--ct-danger-soft)]"
                :title="__('Remover item')"
                :aria-label="__('Remover item')"
                @click="removeChecklistItem(idx)"
              >
                <span class="lucide-trash-2 size-4" aria-hidden="true" />
              </button>
            </div>

            <div class="flex justify-end">
              <Button
                variant="solid"
                size="md"
                :loading="savingChecklist"
                @click="saveChecklist"
              >
                {{ __('Salvar checklist de documentos') }}
              </Button>
            </div>
          </div>

          <!-- Stage gate (Figma 2001:3929): title and the three checks -->
          <div
            class="flex flex-col gap-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span
              class="text-[16px] font-semibold leading-[23px] text-[var(--ct-text-primary)]"
            >
              {{ __('Travas de Governança no Funil (Stage Gate)') }}
            </span>
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


        <!-- ===================================================================== -->
        <!-- SECTION 2: BUREAUS DE CRÉDITO & CREDENCIAIS (SEMPRE VISÍVEIS)        -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'bureaus'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Bureaus de Crédito & Credenciais de API') }}
            </span>
            <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
              {{
                __(
                  'Conecte suas contas nos provedores (DirectD, Serasa Experian, Escavador, Infosimples e CGU) para consultas de Dossiê e Pré-Filtro.',
                )
              }}
            </span>
          </div>

          <!-- 2.1 DirectD Unificado (Token + Relatórios de Dossiê + Pré-Filtro) -->
          <div
            class="space-y-4 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
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

            <!-- Sub-bloco A: Relatórios Completos para o Dossiê (Níveis 1, 2 e 3) -->
            <div class="pt-3 border-t border-outline-gray-2 space-y-2.5">
              <div class="text-p-sm font-semibold text-ink-gray-9">
                {{
                  __(
                    'Relatórios de Bureaus na DirectD por Nível de Profundidade (Pacote Mínimo e Avulsas):',
                  )
                }}
              </div>
              <div
                v-for="bureau in directdBureaus"
                :key="bureau.field"
                class="flex flex-wrap items-center justify-between gap-2 py-1"
              >
                <div class="flex items-center gap-2">
                  <Checkbox
                    v-model="settingsDoc[bureau.field]"
                    :label="bureau.label"
                  />
                  <Badge
                    :label="bureau.tierLabel"
                    :theme="bureau.tierTheme"
                    variant="subtle"
                  />
                </div>
                <span v-if="prices" class="text-p-sm text-ink-gray-6">
                  {{ __('Preço de tabela {0}', [formatMoney(prices[bureau.key])]) }}
                </span>
              </div>
            </div>

            <!-- Sub-bloco B: Consultas de Nível 1 (Triagem Cadastral & Fiscal Barata via DirectD) -->
            <div class="pt-3 border-t border-outline-gray-2 space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-p-sm font-semibold text-ink-gray-9">
                      {{
                        __(
                          'Nível 1 (Triagem Inicial Barata): Regularidade Fiscal & Estadual',
                        )
                      }}
                    </span>
                    <Badge
                      :label="__('Nível 1 · R$ 0,36 a R$ 0,72')"
                      theme="green"
                      variant="subtle"
                    />
                  </div>
                  <p class="text-p-xs text-ink-gray-6">
                    {{
                      __(
                        'Consultas ultrabásicas e baratas para rodar junto com Receita Federal/QSA e CGU CEIS/CNEP (Grátis) antes de gastar com Bureaus de Nível 2 ou 3.',
                      )
                    }}
                  </p>
                </div>
              </div>

              <div class="flex flex-col gap-2.5 pt-1">
                <div class="flex items-center justify-between gap-2 py-1">
                  <Checkbox
                    v-model="settingsDoc.directd_fgts_enabled"
                    :label="__('Regularidade do FGTS / CRF (Caixa)')"
                  />
                  <span v-if="prices" class="text-p-xs font-medium text-ink-gray-7">
                    {{ formatMoney(prices.directd_fgts) }}
                  </span>
                </div>
                <div class="flex items-center justify-between gap-2 py-1">
                  <Checkbox
                    v-model="settingsDoc.directd_sintegra_enabled"
                    :label="__('Sintegra / CCC por UF (Inscrição Estadual)')"
                  />
                  <span v-if="prices" class="text-p-xs font-medium text-ink-gray-7">
                    {{ formatMoney(prices.directd_sintegra) }}
                  </span>
                </div>
              </div>

              <!-- Style Guide "Aviso (toast)" · Informação -->
              <div
                class="flex min-h-11 items-start gap-2.5 rounded-[var(--ct-radius-md)] bg-[var(--ct-accent-soft)] py-2.5 pl-3.5 pr-2.5"
              >
                <span
                  class="lucide-info mt-px size-5 shrink-0 text-[var(--ct-accent)]"
                  aria-hidden="true"
                />
                <p
                  class="mb-0 flex-1 text-[14px] font-medium leading-5 text-[var(--ct-accent)]"
                >
                  <span class="font-semibold">{{
                    __('Proteção Anti-Redundância (economia de R$ 6,43 por consulta):')
                  }}</span>
                  {{
                    __(
                      'O Dossiê QUOD (Nível 2) e o Boa Vista Risco Positivo PJ (Nível 3) já incluem Score, Protestos Detalhados e Ações Judiciais. Por isso, recomendamos manter o pacote legado de Score/Protestos Básicos abaixo desligado na Triagem Nível 1.',
                    )
                  }}
                </p>
              </div>

              <div class="flex items-center justify-between pt-1">
                <div>
                  <div class="text-p-xs font-medium text-ink-gray-7">
                    {{
                      __(
                        'Opcional Legado: Rodar também Score QUOD Avulso + Protestos Básica + Processos Simplificada no Pré-Filtro',
                      )
                    }}
                  </div>
                  <p v-if="prices" class="text-p-xs text-ink-gray-5">
                    {{
                      __('Adiciona score ({0}) + protestos básica ({1}) + processos ({2}) na triagem inicial.',
                        [
                          formatMoney(prices.directd_score),
                          formatMoney(prices.directd_protestos),
                          formatMoney(prices.directd_processos),
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
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
                  {{ __('Serasa Experian · Relatório Avançado PJ') }}
                </span>
              <div class="flex shrink-0 items-center gap-2">
                <Badge
                  :label="__('Contrato Próprio')"
                  theme="amber"
                  variant="subtle"
                />
                <Switch v-model="settingsDoc.serasa_enabled" />
              </div>
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

          <!-- 2.3 Escavador + Infosimples + CGU: one card per row (Figma) -->
          <div class="flex flex-col gap-6">
            <!-- Escavador -->
            <div
              class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
                    {{ __('Busca unificada de processos (Escavador)') }}
                  </span>
                <div class="flex shrink-0 items-center gap-2">
                  <Badge :label="__('Processos')" theme="blue" variant="subtle" />
                  <Switch v-model="settingsDoc.escavador_enabled" />
                </div>
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
              class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
            >
              <div class="flex items-center justify-between">
                <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
                    {{
                      __('Regularidade fiscal e certidões federais (Infosimples)')
                    }}
                  </span>
                <div class="flex shrink-0 items-center gap-2">
                  <Badge :label="__('Fiscal')" theme="blue" variant="subtle" />
                  <Switch v-model="settingsDoc.infosimples_enabled" />
                </div>
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
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
                  {{ __('Etapa 0: Sanções CEIS/CNEP (CGU)') }}
                </span>
              <div class="flex shrink-0 items-center gap-2">
                <Badge :label="__('Grátis')" theme="green" variant="subtle" />
                <Switch v-model="settingsDoc.cgu_enabled" />
              </div>
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


        <!-- ===================================================================== -->
        <!-- SECTION 3: DOSSIÊ DE CRÉDITO & PARECER DA IA (METODOLOGIA 5 Cs)      -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'policy'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Dossiê de Crédito & Parecer da IA') }}
            </span>
            <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
              {{
                __('O que a IA segue para escrever o parecer e as consultas que todo dossiê precisa ter.',
                )
              }}
            </span>
          </div>

          <!-- Minimum package of the credit dossier -->
          <div
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">{{
                __('Pacote mínimo do dossiê (Padrão Nível 2 ou Nível 3)')
              }}</span>
              <div class="flex flex-wrap items-center gap-2">
                <Button
                  variant="subtle"
                  size="sm"
                  @click="applyPackagePreset('tier_2')"
                >
                  {{ __('Preset Nível 2 · Médio (R$ 10,89)') }}
                </Button>
                <Button
                  variant="subtle"
                  size="sm"
                  @click="applyPackagePreset('tier_3_boavista')"
                >
                  {{ __('Preset Nível 3 · Profundo Boa Vista') }}
                </Button>
                <Button
                  variant="subtle"
                  size="sm"
                  @click="applyPackagePreset('tier_3_serasa')"
                >
                  {{ __('Preset Nível 3 · Profundo Serasa') }}
                </Button>
              </div>
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('As consultas padrão que o Dossiê de Crédito executa ao clicar em "Gerar Dossiê". Na tela da empresa/card, o analista também pode escolher em 1 clique entre rodar o Nível 2 (Médio · Dossiê QUOD + SCR Bacen) ou pular direto para o Nível 3 (Profundo · Boa Vista Positivo PJ ou Serasa + SCR + Processos c/ Penhoras + Sócios PF).',
                )
              }}
            </p>
            <!-- Style Guide "Aviso (toast)" · Informação -->
            <div
              class="flex min-h-11 items-start gap-2.5 rounded-[var(--ct-radius-md)] bg-[var(--ct-accent-soft)] py-2.5 pl-3.5 pr-2.5"
            >
              <span
                class="lucide-info mt-px size-5 shrink-0 text-[var(--ct-accent)]"
                aria-hidden="true"
              />
              <p
                class="mb-0 flex-1 text-[14px] font-medium leading-5 text-[var(--ct-accent)]"
              >
                <span class="font-semibold">{{
                  __('Regra Anti-Redundância Nível 3:')
                }}</span>
                {{
                  __(
                    ' No Nível 3 (Profundo), escolha Boa Vista Risco Positivo PJ OU Serasa Relatório Avançado PJ — nunca ambos juntos, pois retornam o mesmo bloco de Score, Faturamento Presumido e Restrições.',
                  )
                }}
              </p>
            </div>
            <template v-if="packageDoc">
              <div class="text-base font-semibold text-ink-gray-9">
                {{ __('Empresa (PJ)') }}
              </div>
              <div
                v-for="opt in packageOptions('company')"
                :key="opt.item"
                class="flex flex-wrap items-center gap-2"
              >
                <Checkbox
                  :model-value="packageDoc.selected[opt.item]"
                  :label="packageOptionLabel(opt)"
                  @update:model-value="(val) => togglePackageItem(opt.item, val)"
                />
                <Badge
                  v-if="opt.item === 'company:dossie_quod' || opt.item === 'company:scr_bacen'"
                  :label="__('Nível 2 · Médio')"
                  theme="blue"
                  variant="subtle"
                />
                <Badge
                  v-else
                  :label="__('Nível 3 · Profundo')"
                  theme="amber"
                  variant="subtle"
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
                {{ __('Sócios / Avalistas (PF — por padrão pré-seleciona apenas o Sócio-Administrador)') }}
              </div>
              <div
                v-for="opt in packageOptions('partners')"
                :key="opt.item"
                class="flex flex-wrap items-center gap-2"
              >
                <Checkbox
                  :model-value="packageDoc.selected[opt.item]"
                  :label="packageOptionLabel(opt)"
                  @update:model-value="(val) => togglePackageItem(opt.item, val)"
                />
                <Badge
                  v-if="opt.item === 'partners:nivel_socioeconomico'"
                  :label="__('Nível 1 · Inicial')"
                  theme="green"
                  variant="subtle"
                />
                <Badge
                  v-else-if="opt.item === 'partners:dossie_quod'"
                  :label="__('Nível 2 · Médio')"
                  theme="blue"
                  variant="subtle"
                />
                <Badge
                  v-else
                  :label="__('Nível 3 · Profundo')"
                  theme="amber"
                  variant="subtle"
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
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex items-center justify-between">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">{{
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

          <!-- Metodologia Configurável do Rating Interno (AA–E) & Calculadora de Limite Sugerido -->
          <div
            v-if="ratingPolicyDoc"
            class="space-y-4 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
                  {{ __('Rating Interno (AA–E) & Calculadora de Limite Sugerido') }}
                </span>
                <Badge
                  :label="
                    ratingPolicyDoc.is_default
                      ? __('Padrão de Mercado')
                      : __('Customizado')
                  "
                  :theme="ratingPolicyDoc.is_default ? 'blue' : 'green'"
                  variant="subtle"
                />
            </div>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __(
                  'Defina as notas de corte (0–1000 pts), o multiplicador sobre o Faturamento Médio Mensal (%) e o limite máximo de concentração por sacado (%) de cada faixa de Rating, além dos tetos de alçada da Mesa de Comitê.',
                )
              }}
            </p>

            <!-- Tabela das Faixas AA a D -->
            <div class="overflow-x-auto border border-outline-gray-2 rounded-[var(--ct-radius-md)]">
              <table class="w-full text-left text-p-sm">
                <thead class="bg-surface-gray-1 text-xs font-semibold text-ink-gray-7 border-b border-outline-gray-2">
                  <tr>
                    <th class="px-3 py-2">{{ __('Faixa') }}</th>
                    <th class="px-3 py-2">{{ __('Score Mínimo (0–1000)') }}</th>
                    <th class="px-3 py-2">{{ __('% s/ Faturamento Mensal') }}</th>
                    <th class="px-3 py-2">{{ __('% Máx. por Sacado') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-outline-gray-1">
                  <tr>
                    <td class="px-3 py-2 font-semibold text-ink-green-3">Rating AA · Risco Mínimo</td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.aa_min_score" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.aa_revenue_pct" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.aa_sacado_pct" type="number" />
                    </td>
                  </tr>
                  <tr>
                    <td class="px-3 py-2 font-semibold text-ink-green-3">Rating A · Risco Baixo</td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.a_min_score" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.a_revenue_pct" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.a_sacado_pct" type="number" />
                    </td>
                  </tr>
                  <tr>
                    <td class="px-3 py-2 font-semibold text-ink-blue-3">Rating B · Risco Moderado</td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.b_min_score" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.b_revenue_pct" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.b_sacado_pct" type="number" />
                    </td>
                  </tr>
                  <tr>
                    <td class="px-3 py-2 font-semibold text-ink-amber-4">Rating C · Exige Garantias</td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.c_min_score" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.c_revenue_pct" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.c_sacado_pct" type="number" />
                    </td>
                  </tr>
                  <tr>
                    <td class="px-3 py-2 font-semibold text-ink-red-3">Rating D · Risco Elevado</td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.d_min_score" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.d_revenue_pct" type="number" />
                    </td>
                    <td class="px-3 py-2">
                      <FormControl v-model.number="ratingPolicyDoc.d_sacado_pct" type="number" />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Tetos e Alçadas do Comitê -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
              <FormControl
                v-model.number="ratingPolicyDoc.max_global_limit"
                type="number"
                :label="__('Teto Global de Limite (R$, 0 = sem teto)')"
              />
              <FormControl
                v-model.number="ratingPolicyDoc.tier_1_max_limit"
                type="number"
                :label="__('Teto Alçada 1 · 1 Voto (R$)')"
              />
              <FormControl
                v-model.number="ratingPolicyDoc.tier_2_max_limit"
                type="number"
                :label="__('Teto Alçada 2 · 2 Votos (R$)')"
              />
              <FormControl
                v-model.number="ratingPolicyDoc.default_validity_days"
                type="number"
                :label="__('Vigência Padrão do Limite (dias)')"
              />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              <Checkbox
                v-model="ratingPolicyDoc.hard_stop_ceis_cnep"
                :label="__('Travar automaticamente em Rating E (R$ 0) se houver Sanção CEIS/CNEP')"
              />
              <Checkbox
                v-model="ratingPolicyDoc.hard_stop_rj_falencia"
                :label="__('Travar automaticamente em Rating E (R$ 0) em caso de Recuperação Judicial / Falência')"
              />
            </div>

            <div class="flex flex-wrap items-center gap-2 pt-2">
              <Button
                variant="solid"
                :loading="savingRatingPolicy"
                @click="saveRatingPolicy(false)"
              >
                {{ __('Salvar metodologia de Rating & Limite') }}
              </Button>
              <Button
                variant="subtle"
                :loading="savingRatingPolicy"
                @click="saveRatingPolicy(true)"
              >
                {{ __('Restaurar Padrão (30% / 22% / 15% / 8% / 3%)') }}
              </Button>
            </div>
          </div>
        </div>


        <!-- ===================================================================== -->
        <!-- SECTION 4: ESTEIRA AUTOMÁTICA DE PRÉ-FILTRO & RÉGUA DE CORTE         -->
        <!-- ===================================================================== -->
        <div
          v-show="activeSection === 'prefilter'"
          class="space-y-6"
        >
          <div class="flex flex-col gap-1">
            <span
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Esteira Automática de Pré-Filtro & Régua de Corte') }}
            </span>
            <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
              {{
                __(
                  'Defina quando a triagem rápida roda sozinha no funil e quais limites disparam alerta ou bloqueio imediato.',
                )
              }}
            </span>
          </div>

          <!-- Master Enable Switch -->
          <div
            class="flex items-center justify-between gap-4 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <div class="flex flex-col gap-1">
              <span
                class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
              >
                {{ __('Ligar a análise de risco e compliance') }}
              </span>
              <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
                {{
                  __('Verificação automática de processos, dívida ativa da União, débitos trabalhistas e protestos em cartório.',
                  )
                }}
              </span>
            </div>
            <Switch v-model="settingsDoc.enabled" />
          </div>

          <!-- Funnel automation trigger -->
          <div
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
              {{ __('Gatilho de automação no funil') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('Roda a verificação automaticamente quando um card entra nesta etapa. Cada verificação automática faz consultas pagas nas suas contas dos provedores.',
                )
              }}
            </p>
            <FormControl
              v-model="settingsDoc.auto_trigger_stage"
              type="text"
              class="max-w-[495px]"
              :label="__('Nome da etapa do gatilho')"
              placeholder="ex: Pré-análise"
            />
            <Checkbox
              v-model="settingsDoc.check_second_organization"
              :label="
                __('Verificar também a segunda organização (sacado), se houver')
              "
            />
          </div>

          <!-- Risk tolerance and blocks -->
          <div
            class="space-y-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]">
              {{ __('Critérios de risco e bloqueios') }}
            </span>
            <p class="text-p-xs text-ink-gray-6">
              {{
                __('Nada reprova sozinho: o sistema avisa e o operador decide. Ligue um bloqueio, ou defina um limite acima de 0, só se a sua política reprova por isso.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <FormControl
                v-model.number="settingsDoc.max_lawsuits_defendant"
                type="number"
                :label="
                  __('Máximo de processos como réu (0 = sem limite, só avisa)')
                "
              />
              <FormControl
                v-model.number="settingsDoc.max_pgfn_debt"
                type="number"
                :label="
                  __('Máximo tolerado de dívida na PGFN (R$) (0 = sem limite, só avisa)',
                  )
                "
              />
            </div>
            <div class="flex flex-col gap-3 pt-1">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="
                  __('Bloquear na hora em caso de recuperação judicial ou falência')
                "
              />
              <Checkbox
                v-model="settingsDoc.block_on_protest"
                :label="__('Bloquear na hora se houver protesto em cartório')"
              />
              <Checkbox
                v-if="settingsDoc.directd_fgts_enabled"
                v-model="settingsDoc.block_on_fgts_irregular"
                :label="__('Bloquear se o FGTS estiver irregular')"
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
import { createDialog } from '@/utils/dialogs'

// Small inline control: CNPJ for the test + "Test connection" button.
const ProviderTest = {
  props: { modelValue: String, loading: Boolean, disabled: Boolean },
  emits: ['update:modelValue', 'test'],
  setup(props, { emit }) {
    return () =>
      // Figma "CNPJ para o teste": labeled 260px field + 48px grey button
      h('div', { class: 'flex items-end gap-2' }, [
        h(FormControl, {
          type: 'text',
          class: 'w-[260px]',
          label: __('CNPJ para o teste'),
          placeholder: '00.000.000/0000-00',
          modelValue: props.modelValue,
          'onUpdate:modelValue': (value) => emit('update:modelValue', value),
        }),
        h(
          Button,
          {
            variant: 'subtle',
            class: '!h-12 !px-7 !text-[16px] !font-semibold',
            loading: props.loading,
            disabled: props.disabled || !props.modelValue,
            onClick: () => emit('test'),
          },
          () => __('Testar conexão'),
        ),
      ])
  },
}

// Figma tabs (no "all" view): one section per tab
const activeSection = ref('funnels')
const sectionTabs = computed(() => [
  { key: 'funnels', label: __('Funis e documentos') },
  { key: 'bureaus', label: __('Bureaus e credenciais') },
  { key: 'policy', label: __('Dossiê e parecer da IA') },
  { key: 'prefilter', label: __('Pré-filtro e régua de corte') },
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
  boavista_acerta_pf_enabled: false,
  dossie_quod_enabled: false,
  scr_bacen_enabled: false,
  processos_completa_enabled: false,
  nivel_socioeconomico_enabled: false,
  allow_paid_extra_opinions: false,
  enforce_checklist_on_stage_gate: false,
  require_verified_checklist_on_committee: false,
  enforce_dossier_on_committee: false,
})

const directdBureaus = [
  {
    key: 'dossie_quod',
    field: 'dossie_quod_enabled',
    label: 'Dossiê QUOD - Completo (Score + Protestos + Negativações + Ações + Cheques)',
    tierLabel: 'Nível 2 · Médio',
    tierTheme: 'blue',
  },
  {
    key: 'scr_bacen',
    field: 'scr_bacen_enabled',
    label: 'SCR Analítico - Resumo BACEN (Endividamento Bancário)',
    tierLabel: 'Nível 2 / 3',
    tierTheme: 'blue',
  },
  {
    key: 'boavista_risco',
    field: 'boavista_risco_enabled',
    label: 'Boa Vista - Risco Positivo PJ (Score Positivo + Faturamento Presumido + Limite)',
    tierLabel: 'Nível 3 · Profundo',
    tierTheme: 'amber',
  },
  {
    key: 'processos_completa',
    field: 'processos_completa_enabled',
    label: 'Processos Judiciais - Completa (com Penhoras e Julgamentos)',
    tierLabel: 'Nível 3 · Profundo',
    tierTheme: 'amber',
  },
  {
    key: 'boavista_acerta_pf',
    field: 'boavista_acerta_pf_enabled',
    label: 'Boa Vista - Acerta Completo Positivo PF (Sócios / Avalistas)',
    tierLabel: 'Nível 3 · Sócios PF',
    tierTheme: 'amber',
  },
  {
    key: 'nivel_socioeconomico',
    field: 'nivel_socioeconomico_enabled',
    label: 'Nível Socioeconômico PF (Faixa de Renda — Triagem Inicial)',
    tierLabel: 'Nível 1 · Inicial',
    tierTheme: 'green',
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
  if (opt.bureau === 'boavista_acerta_pf')
    return Boolean(settingsDoc.value.boavista_acerta_pf_enabled)
  if (opt.bureau === 'processos_completa')
    return Boolean(settingsDoc.value.processos_completa_enabled)
  if (opt.bureau === 'nivel_socioeconomico')
    return Boolean(settingsDoc.value.nivel_socioeconomico_enabled)
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

// Configurable Rating (AA–E) & Suggested Limit Calculator Policy
const ratingPolicyDoc = ref(null)
const originalRatingPolicyJson = ref('')
const savingRatingPolicy = ref(false)

async function loadRatingPolicy() {
  try {
    const res = await call('cred_hub.credit_check.api.get_rating_policy')
    if (res) {
      ratingPolicyDoc.value = {
        ...res,
        hard_stop_ceis_cnep: Boolean(res.hard_stop_ceis_cnep),
        hard_stop_rj_falencia: Boolean(res.hard_stop_rj_falencia),
      }
      originalRatingPolicyJson.value = JSON.stringify(ratingPolicyDoc.value)
    }
  } catch {
    ratingPolicyDoc.value = null
  }
}

async function saveRatingPolicy(resetDefault = false) {
  savingRatingPolicy.value = true
  try {
    const res = await call('cred_hub.credit_check.api.save_rating_policy', {
      policy: resetDefault ? null : JSON.stringify(ratingPolicyDoc.value),
      reset_default: resetDefault ? 1 : 0,
    })
    if (res) {
      ratingPolicyDoc.value = {
        ...res,
        hard_stop_ceis_cnep: Boolean(res.hard_stop_ceis_cnep),
        hard_stop_rj_falencia: Boolean(res.hard_stop_rj_falencia),
      }
      originalRatingPolicyJson.value = JSON.stringify(ratingPolicyDoc.value)
    }
    toast.success(
      resetDefault
        ? __('Metodologia de Rating restaurada para o padrão!')
        : __('Metodologia de Rating & Limite salva com sucesso!'),
    )
  } catch (err) {
    toast.error(
      err?.messages?.[0] ||
        __('Não foi possível salvar a metodologia de Rating.'),
    )
  } finally {
    savingRatingPolicy.value = false
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

function togglePackageItem(item, val) {
  if (!packageDoc.value) return
  packageDoc.value.selected[item] = Boolean(val)
  // Mutual exclusion in Nível 3: Boa Vista Risco Positivo PJ OR Serasa Relatório Avançado PJ
  if (val && item === 'company:boavista_risco') {
    packageDoc.value.selected['company:serasa'] = false
  } else if (val && item === 'company:serasa') {
    packageDoc.value.selected['company:boavista_risco'] = false
  }
}

function applyPackagePreset(presetKey) {
  if (!packageDoc.value) return
  const presets = {
    tier_2: ['company:dossie_quod', 'company:scr_bacen'],
    tier_3_boavista: [
      'company:boavista_risco',
      'company:scr_bacen',
      'company:processos_completa',
      'partners:boavista_acerta_pf',
    ],
    tier_3_serasa: [
      'company:serasa',
      'company:scr_bacen',
      'company:processos_completa',
      'partners:boavista_acerta_pf',
    ],
  }
  const items = presets[presetKey] || presets.tier_2
  for (const key of Object.keys(packageDoc.value.selected)) {
    packageDoc.value.selected[key] = items.includes(key)
  }
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
    settingsDoc.value.directd_fgts_enabled ||
    settingsDoc.value.directd_sintegra_enabled ||
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
  loadRatingPolicy()
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
/* Figma "Caixa de seleção": 20px box, 6px radius */
.ct-credit :deep(input[type='checkbox']) {
  width: 20px;
  height: 20px;
  border-radius: 6px;
}
.ct-credit :deep(label.block) {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-gray-6);
}
</style>
