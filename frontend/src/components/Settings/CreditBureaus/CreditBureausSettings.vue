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
              __(
                'Toda consulta paga usa a sua própria conta em cada provedor: o provedor cobra direto de você e a CredTech não cobra nada. Os preços mostrados são os preços de tabela dos provedores, só como referência; o seu contrato pode ser diferente.',
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
        <!-- TAB 2: BUREAUS E CREDENCIAIS (Figma 2168:13860): only the account of   -->
        <!-- each provider (token, test, on/off). Reports per level have their tab -->
        <!-- ===================================================================== -->
        <div v-show="activeSection === 'bureaus'" class="flex flex-col gap-6">
          <p class="mb-0 text-[14px] leading-5 text-[var(--ct-text-secondary)]">
            {{
              __(
                'Conecte suas contas nos provedores (DirectD, Serasa Experian, Escavador, Infosimples e CGU) para consultas de Dossiê e Pré-Filtro.',
              )
            }}
          </p>

          <!-- DirectD -->
          <div class="ct-provider-card">
            <div class="flex items-center gap-2">
              <span class="ct-provider-title">
                {{
                  __(
                    'DirectD · Dossiê QUOD, SCR Bacen, Boa Vista, Score e Protestos',
                  )
                }}
              </span>
              <span :class="pillClass('accent')">
                {{ __('Principal · Dossiê & Pré-Filtro') }}
              </span>
            </div>
            <p class="ct-provider-text">
              {{
                __(
                  'Score de crédito QUOD, protestos em cartórios de todo o Brasil (IEPTB) e processos.',
                )
              }}
            </p>
            <FormControl
              v-model="settingsDoc.directd_token"
              type="password"
              class="max-w-[1006px]"
              :label="__('Token da API da DirectD')"
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
            <p class="ct-provider-text">
              {{
                __(
                  'O mesmo token vale para a Boa Vista, o Dossiê QUOD e o SCR Bacen da aba Relatórios por nível.',
                )
              }}
            </p>
          </div>

          <!-- Serasa Experian (own contract) -->
          <div class="ct-provider-card">
            <div class="flex items-center gap-2">
              <span class="ct-provider-title">
                {{ __('Serasa Experian · Relatório Avançado PJ') }}
              </span>
              <span :class="pillClass('warning')">{{
                __('Contrato Próprio')
              }}</span>
              <Switch v-model="settingsDoc.serasa_enabled" />
            </div>
            <p class="ct-provider-text">
              {{
                __(
                  'Habilita a consulta ao Relatório Avançado PJ PME diretamente no contrato Serasa Experian da sua empresa.',
                )
              }}
            </p>
            <div
              v-if="settingsDoc.serasa_enabled"
              class="grid grid-cols-1 gap-4 md:grid-cols-2"
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
              <div class="flex items-center gap-3 md:col-span-2">
                <Button
                  variant="subtle"
                  :loading="testing === 'serasa'"
                  :disabled="!settingsDoc.serasa_client_id"
                  @click="testSerasa"
                >
                  {{ __('Testar login') }}
                </Button>
                <span class="ct-provider-text">
                  {{
                    __(
                      'Apenas valida o login na Serasa. Não faz consulta e não tem custo.',
                    )
                  }}
                </span>
              </div>
            </div>
          </div>

          <!-- Escavador -->
          <div class="ct-provider-card">
            <div class="flex items-center gap-2">
              <span class="ct-provider-title">
                {{ __('Pesquisa processual unificada (Escavador)') }}
              </span>
              <span :class="pillClass('accent')">{{ __('Processos') }}</span>
              <Switch v-model="settingsDoc.escavador_enabled" />
            </div>
            <p class="ct-provider-text">
              {{
                __(
                  'Pesquisa tribunais estaduais, federais, trabalhistas e superiores (STJ/STF) em todo o Brasil pelo CNPJ.',
                )
              }}
            </p>
            <p v-if="prices" class="ct-provider-text">
              {{
                __(
                  'Preço de tabela: cerca de {0} por consulta, cobrado pelo Escavador na sua conta.',
                  [formatMoney(prices.escavador)],
                )
              }}
            </p>
            <template v-if="settingsDoc.escavador_enabled">
              <FormControl
                v-model="settingsDoc.escavador_token"
                type="password"
                class="max-w-[1006px]"
                :label="__('Token da API do Escavador')"
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
            </template>
          </div>

          <!-- Infosimples -->
          <div class="ct-provider-card">
            <div class="flex items-center gap-2">
              <span class="ct-provider-title">
                {{
                  __('Regularidade fiscal e certidões federais (Infosimples)')
                }}
              </span>
              <span :class="pillClass('accent')">{{ __('Fiscal') }}</span>
              <Switch v-model="settingsDoc.infosimples_enabled" />
            </div>
            <p class="ct-provider-text">
              {{
                __(
                  'Dívida ativa da União (PGFN), CND Federal, CNDT trabalhista e protestos em cartórios de São Paulo.',
                )
              }}
            </p>
            <p v-if="prices" class="ct-provider-text">
              {{
                __(
                  'Preço de tabela: cerca de {0} por verificação (4 consultas), cobrado pela Infosimples na sua conta.',
                  [formatMoney(prices.infosimples)],
                )
              }}
            </p>
            <template v-if="settingsDoc.infosimples_enabled">
              <FormControl
                v-model="settingsDoc.infosimples_token"
                type="password"
                class="max-w-[1006px]"
                :label="__('Token da API da Infosimples')"
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
            </template>
          </div>

          <!-- CGU CEIS/CNEP (free) -->
          <div class="ct-provider-card">
            <div class="flex items-center gap-2">
              <span class="ct-provider-title">
                {{ __('Etapa 0: sanções CEIS/CNEP (CGU)') }}
              </span>
              <span :class="pillClass('success')">{{ __('Grátis') }}</span>
              <Switch v-model="settingsDoc.cgu_enabled" />
            </div>
            <p class="ct-provider-text">
              {{
                __(
                  'Consulta inicial de sanções públicas (Portal da Transparência). Se a empresa estiver sancionada e o bloqueio estiver ligado, a análise é reprovada na hora.',
                )
              }}
            </p>
            <Checkbox
              v-if="settingsDoc.cgu_enabled"
              v-model="settingsDoc.block_on_ceis_cnep"
              :label="__('Reprovar na hora se constar no CEIS/CNEP')"
            />
          </div>
        </div>

        <!-- ===================================================================== -->
        <!-- TAB 3: RELATÓRIOS POR NÍVEL (Figma 2520:4977): DirectD reports per     -->
        <!-- level and the Nível 1 screening, same fields as before                -->
        <!-- ===================================================================== -->
        <div v-show="activeSection === 'reports'" class="flex flex-col gap-6">
          <p class="mb-0 text-[14px] leading-5 text-[var(--ct-text-secondary)]">
            {{
              __(
                'Escolha quais relatórios entram em cada nível da análise. Aparece só se a integração com a DirectD estiver ligada em Bureaus e credenciais.',
              )
            }}
          </p>

          <div class="flex flex-col gap-3">
            <span class="ct-provider-title">
              {{ __('Relatórios dos bureaus por nível (DirectD)') }}
            </span>

            <div
              class="flex flex-col gap-2.5 border-t border-[var(--ct-border-soft)] pt-3"
            >
              <span class="text-[14px] font-semibold leading-5 text-ink-gray-8">
                {{
                  __(
                    'Relatórios de Bureaus na DirectD por Nível de Profundidade (Pacote Mínimo e Avulsas):',
                  )
                }}
              </span>
              <div
                v-for="bureau in directdBureaus"
                :key="bureau.field"
                class="flex items-center gap-2 py-1"
              >
                <Checkbox
                  v-model="settingsDoc[bureau.field]"
                  :label="bureau.label"
                />
                <span :class="pillClass(bureau.tone)">{{
                  bureau.tierLabel
                }}</span>
                <span class="ct-price">
                  {{ tablePrice(prices?.[bureau.key]) }}
                </span>
              </div>
            </div>

            <div
              class="flex flex-col gap-4 border-t border-[var(--ct-border-soft)] pt-3"
            >
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-2">
                  <span
                    class="text-[14px] font-semibold leading-5 text-ink-gray-8"
                  >
                    {{
                      __(
                        'Nível 1 (Triagem Inicial Barata): Regularidade Fiscal & Estadual',
                      )
                    }}
                  </span>
                  <span :class="pillClass('success')">
                    {{ __('Nível 1 · R$ 0,36 a R$ 0,72') }}
                  </span>
                </div>
                <p
                  class="mb-0 text-[12px] leading-4 text-[var(--ct-text-secondary)]"
                >
                  {{
                    __(
                      'Consultas ultrabásicas e baratas para rodar junto com Receita Federal/QSA e CGU CEIS/CNEP (Grátis) antes de gastar com Bureaus de Nível 2 ou 3.',
                    )
                  }}
                </p>
              </div>

              <div class="flex flex-col gap-2.5">
                <div class="flex items-center gap-2 py-1">
                  <Checkbox
                    v-model="settingsDoc.directd_fgts_enabled"
                    :label="__('Regularidade do FGTS / CRF (Caixa)')"
                  />
                  <span class="ct-price">{{
                    tablePrice(prices?.directd_fgts)
                  }}</span>
                </div>
                <div class="flex items-center gap-2 py-1">
                  <Checkbox
                    v-model="settingsDoc.directd_sintegra_enabled"
                    :label="__('Sintegra / CCC por UF (Inscrição Estadual)')"
                  />
                  <span class="ct-price">
                    {{ tablePrice(prices?.directd_sintegra) }}
                  </span>
                </div>
              </div>

              <!-- Style Guide "Aviso (toast)" · Informação, no button, no close -->
              <div
                class="flex min-h-11 items-center gap-2.5 rounded-[var(--ct-radius-md)] bg-[var(--ct-accent-soft)] py-2.5 pl-3.5 pr-2.5"
              >
                <span
                  class="lucide-info size-5 shrink-0 text-[var(--ct-accent)]"
                  aria-hidden="true"
                />
                <p
                  class="mb-0 flex-1 text-[14px] font-medium leading-5 text-[var(--ct-accent)]"
                >
                  {{
                    __(
                      'Proteção anti-redundância (economia de R$ 6,43 por consulta): o Dossiê QUOD (Nível 2) e o Boa Vista Risco Positivo PJ (Nível 3) já incluem score, protestos detalhados e ações judiciais. Por isso, recomendamos deixar desligado o pacote legado de score e protestos básicos da Triagem Nível 1.',
                    )
                  }}
                </p>
              </div>

              <div class="flex items-center gap-[17px]">
                <Switch
                  v-model="settingsDoc.directd_enabled"
                  class="shrink-0"
                />
                <div class="flex flex-col gap-0.5 text-[12px] leading-4">
                  <span class="font-medium text-ink-gray-7">
                    {{
                      __(
                        'Opcional Legado: Rodar também Score QUOD Avulso + Protestos Básica + Processos Simplificada no Pré-Filtro',
                      )
                    }}
                  </span>
                  <span v-if="prices" class="text-[var(--ct-text-tertiary)]">
                    {{
                      __(
                        'Adiciona score ({0}) + protestos básica ({1}) + processos ({2}) na triagem inicial.',
                        [
                          formatMoney(prices.directd_score),
                          formatMoney(prices.directd_protestos),
                          formatMoney(prices.directd_processos),
                        ],
                      )
                    }}
                  </span>
                </div>
              </div>

              <FormControl
                v-if="settingsDoc.directd_enabled"
                v-model.number="settingsDoc.min_directd_score"
                type="number"
                class="w-[495px] max-w-full"
                :label="__('Score mínimo (0 = nunca reprovar por score)')"
              />

              <p
                v-if="usesDirectd && !settingsDoc.directd_token"
                class="mb-0 text-[14px] font-medium leading-5 text-[var(--ct-warning)]"
              >
                {{
                  __(
                    'Informe o token da DirectD em Bureaus e credenciais e clique em Salvar para usar os relatórios marcados.',
                  )
                }}
              </p>
            </div>
          </div>
        </div>

        <!-- ===================================================================== -->
        <!-- TAB 4: DOSSIÊ E PARECER DA IA (Figma 2167:13315): sections split by    -->
        <!-- divider lines, no card boxes                                          -->
        <!-- ===================================================================== -->
        <div v-show="activeSection === 'policy'" class="flex flex-col gap-6">
          <div class="flex flex-col gap-1">
            <span
              class="text-[18px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Dossiê de Crédito & Parecer da IA') }}
            </span>
            <span class="text-[14px] leading-5 text-[var(--ct-text-secondary)]">
              {{
                __(
                  'O que a IA segue para escrever o parecer e as consultas que todo dossiê precisa ter.',
                )
              }}
            </span>
          </div>

          <!-- Minimum package of the credit dossier -->
          <div class="flex flex-col gap-[18px]">
            <span class="ct-provider-title">
              {{ __('Pacote mínimo do dossiê (Padrão Nível 2 ou Nível 3)') }}
            </span>
            <!-- Figma "Botão de opção": one preset at a time -->
            <div class="flex flex-wrap items-center gap-6" role="radiogroup">
              <label
                v-for="preset in packagePresets"
                :key="preset.key"
                class="flex cursor-pointer items-center gap-2 text-[14px] text-[var(--ct-text-primary)]"
              >
                <input
                  type="radio"
                  name="ct-package-preset"
                  class="ct-radio"
                  :value="preset.key"
                  :checked="activePreset === preset.key"
                  :disabled="!packageDoc"
                  @change="applyPackagePreset(preset.key)"
                />
                {{ preset.label }}
              </label>
            </div>
            <p
              class="mb-0 text-[12px] leading-4 text-[var(--ct-text-secondary)]"
            >
              {{
                __(
                  'As consultas padrão que o Dossiê de Crédito executa ao clicar em "Gerar Dossiê". Na tela da empresa/card, o analista também pode escolher em 1 clique entre rodar o Nível 2 (Médio · Dossiê QUOD + SCR Bacen) ou pular direto para o Nível 3 (Profundo · Boa Vista Positivo PJ ou Serasa + SCR + Processos c/ Penhoras + Sócios PF).',
                )
              }}
            </p>
            <template v-if="packageDoc">
              <span
                class="text-[14px] font-semibold leading-5 text-[var(--ct-text-primary)]"
              >
                {{ __('Empresa (PJ)') }}
              </span>
              <div
                v-for="opt in visiblePackageOptions('company')"
                :key="opt.item"
                class="flex flex-wrap items-center gap-2"
              >
                <Checkbox
                  :model-value="packageDoc.selected[opt.item]"
                  :label="packageOptionLabel(opt)"
                  @update:model-value="
                    (val) => togglePackageItem(opt.item, val)
                  "
                />
                <span :class="pillClass(packageTier(opt).tone)">
                  {{ packageTier(opt).label }}
                </span>
                <span
                  v-if="!isOptionConfigured(opt)"
                  class="text-[12px] font-medium leading-4 text-[var(--ct-warning)]"
                >
                  {{ packageOptionWarning(opt) }}
                </span>
              </div>
              <template v-if="visiblePackageOptions('partners').length">
                <span
                  class="text-[14px] font-semibold leading-5 text-[var(--ct-text-primary)]"
                >
                  {{
                    __(
                      'Sócios / Avalistas (PF — por padrão pré-seleciona apenas o Sócio-Administrador)',
                    )
                  }}
                </span>
                <div
                  v-for="opt in visiblePackageOptions('partners')"
                  :key="opt.item"
                  class="flex flex-wrap items-center gap-2"
                >
                  <Checkbox
                    :model-value="packageDoc.selected[opt.item]"
                    :label="packageOptionLabel(opt)"
                    @update:model-value="
                      (val) => togglePackageItem(opt.item, val)
                    "
                  />
                  <span :class="pillClass(packageTier(opt).tone)">
                    {{ packageTier(opt).label }}
                  </span>
                  <span
                    v-if="!isOptionConfigured(opt)"
                    class="text-[12px] font-medium leading-4 text-[var(--ct-warning)]"
                  >
                    {{ packageOptionWarning(opt) }}
                  </span>
                </div>
              </template>
              <FormControl
                v-model.number="packageDoc.reuse_days"
                type="number"
                class="w-[314px] max-w-full"
                :label="
                  __(
                    'Reaproveitar consultas feitas há até quantos dias (0 = sempre consultar de novo)',
                  )
                "
              />
              <p
                class="mb-0 text-[14px] leading-5 text-[var(--ct-text-primary)]"
              >
                {{ packageCostText }}
              </p>
              <div>
                <Button
                  variant="solid"
                  :loading="savingPackage"
                  @click="savePackage"
                >
                  {{ __('Salvar pacote') }}
                </Button>
              </div>
            </template>
          </div>

          <!-- Figma "Divisor" · Linha -->
          <div class="flex h-5 items-center" aria-hidden="true">
            <div class="h-px flex-1 bg-[var(--ct-border)]" />
          </div>

          <!-- Credit policy the AI follows -->
          <div class="flex flex-col gap-[18px]">
            <span class="ct-provider-title">
              {{ __('Política de crédito (parecer da IA)') }}
            </span>
            <p
              class="mb-0 text-[12px] leading-4 text-[var(--ct-text-secondary)]"
            >
              {{
                __(
                  'A IA escreve o parecer de crédito seguindo esta metodologia. Os parâmetros viram alertas automáticos no parecer e nunca reprovam sozinhos (0 = sem limite). Cada vez que você salva nasce uma versão nova, e cada parecer guarda a versão que usou.',
                )
              }}
            </p>
            <template v-if="policyDoc">
              <FormControl
                v-model="policyDoc.methodology"
                type="textarea"
                :rows="4"
                class="w-[822px] max-w-full"
                :label="__('Metodologia')"
              />
              <div class="flex flex-col gap-4">
                <div class="flex flex-wrap items-start gap-4">
                  <FormControl
                    v-model.number="policyDoc.parameters.min_company_age_months"
                    type="number"
                    class="w-[280px]"
                    :label="__('Idade mínima da empresa (meses)')"
                  />
                  <FormControl
                    v-model.number="
                      policyDoc.parameters.max_scr_overdue_percent
                    "
                    type="number"
                    class="w-[280px]"
                    :label="__('Máx. de dívida vencida no SCR (%)')"
                  />
                </div>
                <div class="flex flex-wrap items-center gap-4">
                  <div class="flex items-center gap-2">
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
                  <Checkbox
                    v-model="policyDoc.parameters.alert_partner_restrictions"
                    :label="__('Alertar quando um sócio tiver restrições')"
                  />
                </div>
              </div>
              <div class="flex flex-col gap-0.5">
                <Checkbox
                  v-model="settingsDoc.allow_paid_extra_opinions"
                  :label="__('Permitir pareceres extras pagos')"
                />
                <p
                  class="mb-0 max-w-[753px] pl-[26px] text-[12px] leading-4 text-[var(--ct-text-secondary)]"
                >
                  {{
                    __(
                      'Cada empresa tem 30 pareceres da IA por mês incluídos. Com isto ligado, a partir do 31º cada parecer custa R$ 3,00 da carteira de créditos, com confirmação antes. Desligado, o parecer para até o mês seguinte. Salve as configurações para valer.',
                    )
                  }}
                </p>
              </div>
            </template>
          </div>

          <template v-if="ratingPolicyDoc">
            <!-- Figma "Divisor" · Linha -->
            <div class="flex h-5 items-center" aria-hidden="true">
              <div class="h-px flex-1 bg-[var(--ct-border)]" />
            </div>

            <!-- Internal rating (AA–E) and suggested limit calculator -->
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-2">
                <span
                  class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
                >
                  {{
                    __('Rating Interno (AA–E) & Calculadora de Limite Sugerido')
                  }}
                </span>
                <span
                  :class="
                    pillClass(ratingPolicyDoc.is_default ? 'accent' : 'success')
                  "
                >
                  {{
                    ratingPolicyDoc.is_default
                      ? __('Padrão de Mercado')
                      : __('Customizado')
                  }}
                </span>
              </div>
              <p
                class="mb-0 text-[12px] leading-4 text-[var(--ct-text-secondary)]"
              >
                {{
                  __(
                    'Defina as notas de corte (0–1000 pts), o multiplicador sobre o Faturamento Médio Mensal (%) e o limite máximo de concentração por sacado (%) de cada faixa de Rating, além dos tetos de alçada da Mesa de Comitê.',
                  )
                }}
              </p>

              <!-- Bands AA to D -->
              <div
                class="ct-rating-table overflow-hidden rounded-[var(--ct-radius-md)] border border-[var(--ct-border-soft)]"
              >
                <table class="w-full table-fixed text-left">
                  <thead
                    class="border-b border-[var(--ct-border-soft)] bg-[var(--ct-bg-soft)]"
                  >
                    <tr>
                      <th
                        v-for="column in ratingColumns"
                        :key="column"
                        class="px-3 py-2 text-[12px] font-semibold leading-4 text-ink-gray-7"
                      >
                        {{ column }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(band, idx) in ratingBands"
                      :key="band.key"
                      :class="idx ? 'border-t border-[#ededf0]' : ''"
                    >
                      <td class="px-3 py-2">
                        <span
                          class="flex items-center gap-2 whitespace-nowrap text-[14px] leading-5 text-[var(--ct-text-primary)]"
                        >
                          <span
                            class="size-2 shrink-0 rounded-full"
                            :style="{ backgroundColor: band.color }"
                          />
                          {{ band.label }}
                        </span>
                      </td>
                      <td class="px-3 py-2">
                        <FormControl
                          v-model.number="
                            ratingPolicyDoc[`${band.key}_min_score`]
                          "
                          type="number"
                        />
                      </td>
                      <td class="px-3 py-2">
                        <FormControl
                          v-model.number="
                            ratingPolicyDoc[`${band.key}_revenue_pct`]
                          "
                          type="number"
                        />
                      </td>
                      <td class="px-3 py-2">
                        <FormControl
                          v-model.number="
                            ratingPolicyDoc[`${band.key}_sacado_pct`]
                          "
                          type="number"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Committee ceilings -->
              <div class="grid grid-cols-1 gap-3 md:grid-cols-4">
                <FormControl
                  v-model.number="ratingPolicyDoc.max_global_limit"
                  type="number"
                  :label="__('Teto Global de Limite')"
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

              <div class="grid grid-cols-1 items-center gap-3 md:grid-cols-2">
                <Checkbox
                  v-model="ratingPolicyDoc.hard_stop_ceis_cnep"
                  :label="
                    __(
                      'Travar automaticamente em Rating E (R$ 0) se houver Sanção CEIS/CNEP',
                    )
                  "
                />
                <Checkbox
                  v-model="ratingPolicyDoc.hard_stop_rj_falencia"
                  :label="
                    __(
                      'Travar automaticamente em Rating E (R$ 0) em caso de Recuperação Judicial / Falência',
                    )
                  "
                />
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <Button
                  variant="solid"
                  :loading="savingRatingPolicy"
                  @click="saveRatingPolicy(false)"
                >
                  {{ __('Salvar metodologia') }}
                </Button>
                <Button
                  variant="subtle"
                  :loading="savingRatingPolicy"
                  @click="saveRatingPolicy(true)"
                >
                  {{ __('Restaurar Padrão') }}
                </Button>
              </div>
            </div>
          </template>
        </div>

        <!-- ===================================================================== -->
        <!-- SECTION 4: ESTEIRA AUTOMÁTICA DE PRÉ-FILTRO & RÉGUA DE CORTE         -->
        <!-- ===================================================================== -->
        <div v-show="activeSection === 'prefilter'" class="space-y-6">
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

          <!-- Master Enable Switch: Figma "Análise de risco e compliance"
               (2324:25139) is a gray panel without border -->
          <div
            class="flex items-center justify-between gap-4 rounded-[var(--ct-radius-md)] bg-[var(--ct-bg-soft)] px-5 py-4"
          >
            <div class="flex flex-col gap-1">
              <span
                class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
              >
                {{ __('Ligar a análise de risco e compliance') }}
              </span>
              <span
                class="text-[14px] leading-5 text-[var(--ct-text-secondary)]"
              >
                {{
                  __(
                    'Verificação automática de processos, dívida ativa da União, débitos trabalhistas e protestos em cartório.',
                  )
                }}
              </span>
            </div>
            <Switch v-model="settingsDoc.enabled" size="md" />
          </div>

          <!-- Funnel automation trigger (Figma "Gatilho de automação no funil":
               12px apart, 12px help text, 495px field) -->
          <div
            class="flex flex-col gap-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span
              class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Gatilho de automação no funil') }}
            </span>
            <p class="text-xs text-ink-gray-6">
              {{
                __(
                  'Roda a verificação automaticamente quando um card entra nesta etapa. Cada verificação automática faz consultas pagas nas suas contas dos provedores.',
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

          <!-- Risk tolerance and blocks (Figma "Critérios de risco e bloqueios":
               12px apart, two 495px fields) -->
          <div
            class="flex flex-col gap-3 rounded-[var(--ct-radius-md)] border border-[var(--ct-border)] bg-surface-white px-5 py-4"
          >
            <span
              class="text-[16px] font-semibold leading-6 text-[var(--ct-text-primary)]"
            >
              {{ __('Critérios de risco e bloqueios') }}
            </span>
            <p class="text-xs text-ink-gray-6">
              {{
                __(
                  'Nada reprova sozinho: o sistema avisa e o operador decide. Ligue um bloqueio, ou defina um limite acima de 0, só se a sua política reprova por isso.',
                )
              }}
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:pr-8">
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
                  __(
                    'Máximo tolerado de dívida na PGFN (R$) (0 = sem limite, só avisa)',
                  )
                "
              />
            </div>
            <div class="flex flex-col gap-3">
              <Checkbox
                v-model="settingsDoc.block_on_bankruptcy"
                :label="
                  __(
                    'Bloquear na hora em caso de recuperação judicial ou falência',
                  )
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
  { key: 'reports', label: __('Relatórios por nível') },
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

// Figma "Relatórios por nível" (2520:4977): order and level pill of each report
const directdBureaus = [
  {
    key: 'boavista_risco',
    field: 'boavista_risco_enabled',
    label:
      'Boa Vista - Risco Positivo PJ (Score Positivo + Faturamento Presumido + Limite)',
    tierLabel: 'Nível 3 · Profundo',
    tone: 'warning',
  },
  {
    key: 'dossie_quod',
    field: 'dossie_quod_enabled',
    label:
      'Dossiê QUOD - Completo (Score + Protestos + Negativações + Ações + Cheques)',
    tierLabel: 'Nível 2 · Médio',
    tone: 'accent',
  },
  {
    key: 'scr_bacen',
    field: 'scr_bacen_enabled',
    label: 'SCR Analítico - Resumo BACEN (Endividamento Bancário)',
    tierLabel: 'Nível 2 / 3',
    tone: 'accent',
  },
  {
    key: 'processos_completa',
    field: 'processos_completa_enabled',
    label: 'Processos Judiciais - Completa (com Penhoras e Julgamentos)',
    tierLabel: 'Nível 3 · Profundo',
    tone: 'warning',
  },
  {
    key: 'boavista_acerta_pf',
    field: 'boavista_acerta_pf_enabled',
    label: 'Boa Vista - Acerta Completo Positivo PF (Sócios / Avalistas)',
    tierLabel: 'Nível 3 · Sócios PF',
    tone: 'warning',
  },
  {
    key: 'nivel_socioeconomico',
    field: 'nivel_socioeconomico_enabled',
    label: 'Nível Socioeconômico PF (Faixa de Renda — Triagem Inicial)',
    tierLabel: 'Nível 1 · Inicial',
    tone: 'success',
  },
]

// Style Guide "Pílula de status": 12 Medium, 10px/2px padding, pill corners
const PILL_TONES = {
  accent: 'bg-[var(--ct-bg-selected)] text-[var(--ct-text-accent)]',
  success: 'bg-[var(--ct-success-soft)] text-[var(--ct-success)]',
  warning: 'bg-[var(--ct-warning-soft)] text-[var(--ct-warning)]',
}
function pillClass(tone) {
  return [
    'inline-flex shrink-0 items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-[12px] font-medium leading-4',
    PILL_TONES[tone] || PILL_TONES.accent,
  ]
}

function tablePrice(value) {
  return value
    ? __('Preço de tabela {0}', [formatMoney(value)])
    : __('Preço de tabela —')
}

// Rating table (Figma 2167:13982): band label with an 8px colored dot
const ratingColumns = computed(() => [
  __('Faixa'),
  __('Score Mínimo (0–1000)'),
  __('% s/ Faturamento Mensal'),
  __('% Máx. por Sacado'),
])
const ratingBands = [
  {
    key: 'aa',
    label: 'Rating AA · Risco Mínimo',
    color: 'var(--ct-status-green)',
  },
  {
    key: 'a',
    label: 'Rating A · Risco Baixo',
    color: 'var(--ct-status-green)',
  },
  {
    key: 'b',
    label: 'Rating B · Risco Moderado',
    color: 'var(--ct-status-blue)',
  },
  {
    key: 'c',
    label: 'Rating C · Exige Garantias',
    color: 'var(--ct-status-orange)',
  },
  {
    key: 'd',
    label: 'Rating D · Risco Elevado',
    color: 'var(--ct-status-red)',
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
    toast.error(
      err?.messages?.[0] ||
        __('Não foi possível salvar a política de crédito.'),
    )
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
    activePreset.value = detectPreset(selected)
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

const PACKAGE_PRESETS = {
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
const packagePresets = computed(() => [
  { key: 'tier_2', label: __('Nível 2 · Médio (R$ 10,89)') },
  { key: 'tier_3_boavista', label: __('Nível 3 · Profundo Boa Vista') },
  { key: 'tier_3_serasa', label: __('Nível 3 · Profundo Serasa') },
])
// The radio shows which preset the saved package follows (Serasa or Boa Vista = Nível 3)
const activePreset = ref('tier_2')
function detectPreset(selected) {
  if (selected['company:serasa']) return 'tier_3_serasa'
  if (selected['company:boavista_risco']) return 'tier_3_boavista'
  return 'tier_2'
}

function applyPackagePreset(presetKey) {
  if (!packageDoc.value) return
  activePreset.value = presetKey
  const items = PACKAGE_PRESETS[presetKey] || PACKAGE_PRESETS.tier_2
  for (const key of Object.keys(packageDoc.value.selected)) {
    packageDoc.value.selected[key] = items.includes(key)
  }
}

// Only the reports of the chosen level are listed, plus anything already ticked
function visiblePackageOptions(scope) {
  const presetItems = PACKAGE_PRESETS[activePreset.value] || []
  return packageOptions(scope).filter(
    (opt) =>
      presetItems.includes(opt.item) || packageDoc.value?.selected[opt.item],
  )
}

function packageTier(opt) {
  if (opt.item === 'partners:nivel_socioeconomico')
    return { label: __('Nível 1 · Inicial'), tone: 'success' }
  if (
    [
      'company:dossie_quod',
      'company:scr_bacen',
      'partners:dossie_quod',
    ].includes(opt.item)
  )
    return { label: __('Nível 2 · Médio'), tone: 'accent' }
  return { label: __('Nível 3 · Profundo'), tone: 'warning' }
}

function packageOptionWarning(opt) {
  if (isOptionEnabled(opt))
    return __('falta informar o token/credencial em Bureaus e credenciais')
  return opt.bureau === 'serasa'
    ? __('ligue a Serasa em Bureaus e credenciais')
    : __('ligue este relatório em Relatórios por nível')
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
  let text = __(
    'Cerca de {0} por empresa pelo preço de tabela, cobrado pelo provedor na sua conta.',
    [formatMoney(sum('company'))],
  )
  if (sum('partners'))
    text +=
      ' ' +
      __('Mais {0} por cada sócio com CPF.', [formatMoney(sum('partners'))])
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
    toast.error(
      err?.messages?.[0] || __('Não foi possível salvar o pacote mínimo.'),
    )
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
    toast.error(
      err?.messages?.[0] || __('Falha ao salvar as configurações de crédito.'),
    )
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
    message: __(
      'O teste executa uma consulta real no CNPJ {0}, cobrada por {1} na sua conta (preço de tabela cerca de {2}). A CredTech não cobra nada.',
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
  margin-top: 0;
  border-radius: 6px;
}
/* its label: 14/20 Regular, black (Figma 2324:25139) */
.ct-credit :deep(input[type='checkbox'] + label) {
  font-weight: 400;
  line-height: 20px;
  color: var(--ct-text-primary);
}
.ct-credit :deep(label.block) {
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  color: var(--ink-gray-6);
}
/* Figma provider card (Bureaus e credenciais): 8px radius, 20/16 padding */
.ct-provider-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 20px;
  border: 1px solid var(--ct-border);
  border-radius: var(--ct-radius-md);
  background: var(--ct-bg-page);
}
.ct-provider-title {
  flex: 1;
  min-width: 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
  color: var(--ct-text-primary);
}
.ct-provider-text {
  margin: 0;
  font-size: 12px;
  line-height: 16px;
  color: var(--ct-text-secondary);
}
/* "Preço de tabela" pushed to the right end of each report row */
.ct-price {
  margin-left: auto;
  padding-left: 16px;
  font-size: 12px;
  line-height: 16px;
  white-space: nowrap;
  color: var(--ct-text-secondary);
}
/* Rating table inputs (Figma "Entrada"): 34px, 14px text, 10px padding */
.ct-credit
  .ct-rating-table
  :deep(input:not([type='checkbox']):not([type='radio'])) {
  height: 34px;
  font-size: 14px;
  padding-inline: 10px;
}
</style>
