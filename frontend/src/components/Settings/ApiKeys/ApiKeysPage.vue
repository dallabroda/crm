<template>
  <!-- Figma "Configurações · API" (2336:11101): the keys as a "Tabela"; the
       reference and the audit live on "Documentação da API" (2345:29277),
       opened from the top bar, with "Voltar" -->
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="view === 'docs' ? __('API documentation') : __('API')">
      <template v-if="view === 'docs'" #title>
        <div class="flex min-w-0 items-center gap-3">
          <SettingsBackLink @click="view = 'keys'" />
          <h1 class="truncate">{{ __('API documentation') }}</h1>
        </div>
      </template>
      <template #description>
        {{
          view === 'docs'
            ? __(
                'Integre seu ERP, site, motor de crédito ou data warehouse com autenticação Bearer, isolamento por funil, operações em lote (Batch) e sincronização incremental.',
              )
            : __(
                'Keys for other systems to read and write your cards, contacts and organizations. Each key only reaches the funnels you choose and does not take a user seat.',
              )
        }}
      </template>
      <template #actions>
        <div v-if="view === 'docs'" class="flex items-center gap-2">
          <Button
            variant="outline"
            icon-right="lucide-external-link"
            :label="__('OpenAPI 3.1 (JSON)')"
            href="/api/method/cred_hub.api_keys.get_openapi_spec"
          />
          <Button
            variant="solid"
            icon-right="lucide-external-link"
            :label="__('Open playground')"
            href="/api-docs"
          />
        </div>
        <div v-else class="flex items-center gap-2">
          <Button
            variant="outline"
            icon-right="lucide-external-link"
            :label="__('API documentation')"
            @click="view = 'docs'"
          />
          <Button
            v-if="data"
            variant="solid"
            icon-left="lucide-plus"
            :label="__('New key')"
            :disabled="activeCount >= data.limit"
            @click="openForm()"
          />
        </div>
      </template>
    </SettingsPageHeader>

    <div v-if="!data" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="apiKeys.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>

    <div v-else-if="view === 'keys'" class="flex flex-col gap-4 overflow-y-auto">
      <!-- Old keys (token of a user, made in the technical screen) stop on a date set on deploy -->
      <div
        v-if="data.legacy_until && data.legacy_users.length"
        class="rounded px-4 py-3 text-p-base"
        :class="
          legacyStopped(data.legacy_until)
            ? 'bg-surface-red-1 text-ink-red-7'
            : 'bg-surface-amber-1 text-ink-amber-7'
        "
      >
        <p class="text-base-semibold">
          {{
            legacyStopped(data.legacy_until)
              ? __('The old API keys stopped on {0}.', [
                  dayMonth(data.legacy_until),
                ])
              : __('The old API keys stop on {0}.', [
                  dayMonth(data.legacy_until),
                ])
          }}
        </p>
        <p class="mt-1 text-p-sm">
          {{
            __(
              'Create a key here for each integration and replace it in the system that uses it. Users with an old key: {0}.',
              [data.legacy_users.map((u) => u.full_name || u.name).join(', ')],
            )
          }}
        </p>
      </div>

      <p v-if="activeCount >= data.limit" class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Your company can have up to {0} active keys. Revoke one to create another.',
            [data.limit],
          )
        }}
      </p>

      <SettingsEmptyState
        v-if="!data.keys.length"
        :icon="LucideKeyRound"
        :title="__('No API keys yet.')"
        :description="__('Create a key to connect other systems to the CRM.')"
        :action-label="__('New key')"
        @action="openForm()"
      />

      <!-- Figma "Tabela": grey 40px header (12 Medium), 52px rows; the name
           opens the key (edit, new secret), its details are in the tooltip -->
      <div
        v-else
        class="overflow-hidden rounded-lg border border-[var(--ct-border)]"
      >
        <div
          class="ct-api-keys-grid h-10 items-center border-b border-[var(--ct-border)] bg-[var(--ct-bg-soft)] text-[12px] font-medium leading-4 text-[color:var(--ct-text-secondary)]"
        >
          <span>{{ __('Name') }}</span>
          <span>{{ __('Key') }}</span>
          <span>{{ __('Created on') }}</span>
          <span>{{ __('Last used') }}</span>
          <span />
        </div>
        <div
          v-for="key in data.keys"
          :key="key.name"
          class="ct-api-keys-grid min-h-[52px] items-center border-b border-[var(--ct-border)] py-2.5 text-[14px] leading-5 text-[color:var(--ct-text-secondary)] last:border-b-0"
          :class="{ 'opacity-60': key.status !== 'Active' }"
        >
          <Tooltip :text="keyDetails(key)">
            <button
              type="button"
              class="min-w-0 truncate text-left font-medium text-[color:var(--ct-text-primary)] hover:underline disabled:hover:no-underline"
              :disabled="key.status !== 'Active'"
              @click="openForm(key)"
            >
              {{ key.label }}
            </button>
          </Tooltip>
          <span class="truncate">
            {{ key.prefix }}…{{ key.secret_hint }}
          </span>
          <span>{{ brDate(key.created_on) }}</span>
          <span>
            {{ key.last_used_on ? timeAgo(key.last_used_on) : __('never') }}
          </span>
          <div class="flex justify-start">
            <Button
              v-if="key.status === 'Active'"
              variant="subtle"
              theme="red"
              class="whitespace-nowrap"
              :label="
                confirm.revoke === key.name
                  ? __('Confirm revoke')
                  : __('Revoke')
              "
              :loading="busy === key.name + ':revoke'"
              @click="revoke(key)"
              @blur="confirm.revoke = null"
            />
            <Badge
              v-else
              :label="__('Revoked')"
              theme="gray"
              variant="subtle"
            />
          </div>
        </div>
      </div>
      <p v-if="confirm.revoke" class="text-p-sm text-ink-red-6">
        {{ __('The key stops working right away. This cannot be undone.') }}
      </p>
    </div>

    <!-- Figma "Documentação da API" (2345:29277): reference (3 mini cards,
         tabs, endpoints) and the audit card, 32px apart -->
    <div v-else class="mt-2 flex flex-col gap-8 overflow-y-auto">
      <div class="flex flex-col gap-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div
          class="flex flex-col gap-1.5 rounded-lg border border-[var(--ct-border)] p-3"
        >
          <div
            class="text-[12px] font-medium uppercase leading-[18px] tracking-[0.1em] text-ink-gray-9"
          >
            {{ __('URL Base') }}
          </div>
          <div class="flex h-[17px] items-center justify-between gap-2">
            <code class="truncate font-mono text-[12px] font-medium leading-[17px] text-ink-gray-9">{{ baseUrl }}</code>
            <Button
              size="sm"
              variant="ghost"
              icon="lucide-copy"
              :tooltip="__('Copy')"
              @click="copyToClipboard(baseUrl)"
            />
          </div>
        </div>
        <div
          class="flex flex-col gap-1.5 rounded-lg border border-[var(--ct-border)] p-3"
        >
          <div
            class="text-[12px] font-medium uppercase leading-[18px] tracking-[0.1em] text-ink-gray-9"
          >
            {{ __('Cabeçalho de Autenticação') }}
          </div>
          <div class="truncate font-mono text-[12px] font-medium leading-[17px] text-ink-gray-9">
            Authorization: Bearer hub_&lt;id&gt;_&lt;segredo&gt;
          </div>
        </div>
        <div
          class="flex flex-col gap-1.5 rounded-lg border border-[var(--ct-border)] p-3"
        >
          <div
            class="text-[12px] font-medium uppercase leading-[18px] tracking-[0.1em] text-ink-gray-9"
          >
            {{ __('Rate Limit (Janela Deslizante)') }}
          </div>
          <div class="truncate text-[12px] font-medium leading-[17px] text-ink-gray-9">
            {{ __('300 chamadas/min (leitura) · 60 escritas/min por chave') }}
          </div>
        </div>
      </div>

      <!-- Figma "Abas" -->
      <div
        class="flex flex-wrap items-start gap-4 border-b border-[var(--ct-border)]"
        role="tablist"
      >
        <button
          v-for="section in docSections"
          :key="section.id"
          type="button"
          role="tab"
          :aria-selected="activeDocTab === section.id"
          class="flex flex-col"
          @click="activeDocTab = section.id"
        >
          <span
            class="px-1 py-2.5 text-[14px] font-medium leading-5"
            :class="
              activeDocTab === section.id
                ? 'text-[color:var(--ct-text-accent)]'
                : 'text-[color:var(--ct-text-secondary)] hover:text-[color:var(--ct-text-primary)]'
            "
          >
            {{ section.title }}
          </span>
          <span
            class="h-0.5 w-full"
            :class="activeDocTab === section.id ? 'bg-[var(--ct-accent)]' : ''"
          />
        </button>
      </div>

      <div v-if="currentDocSection" class="flex flex-col gap-6">
        <div
          v-for="ep in currentDocSection.endpoints"
          :key="ep.path"
          class="flex flex-col gap-2 rounded-lg border border-[var(--ct-border)] px-4 py-3.5"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <Badge
                :label="ep.method"
                :theme="ep.method === 'GET' ? 'blue' : ep.method === 'DELETE' ? 'red' : 'green'"
                variant="subtle"
              />
              <code class="font-mono text-[13px] font-semibold text-ink-gray-9">{{ ep.path }}</code>
            </div>
            <span class="text-[12px] leading-4 text-ink-gray-9">
              {{ __('Escopo:') }} {{ ep.scope }}
            </span>
          </div>
          <p class="text-[14px] leading-5 text-ink-gray-9">{{ ep.desc }}</p>
          <div
            v-if="ep.curl"
            class="relative rounded-md bg-[var(--ct-bg-soft)] px-3 py-2.5 font-mono text-[12px] font-medium leading-[18px] text-ink-gray-9 overflow-x-auto whitespace-pre"
          >{{ ep.curl }}</div>
        </div>
      </div>

      </div>

      <!-- Live API Audit & Telemetry Logs -->
      <div class="flex flex-col gap-3.5 rounded-lg border border-[var(--ct-border)] p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-[16px] font-semibold leading-[23px] text-ink-gray-9">
              {{ __('Auditoria e Últimas Chamadas da API') }}
            </span>
            <Badge
              v-if="auditMetrics"
              :label="__('{0} chamadas (24h)', [auditMetrics.total_24h || 0])"
              theme="blue"
              variant="subtle"
            />
            <Badge
              v-if="auditMetrics && auditMetrics.errors_24h > 0"
              :label="__('{0} erros (24h)', [auditMetrics.errors_24h])"
              theme="red"
              variant="subtle"
            />
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model="selectedLogKey"
              class="h-[33px] rounded-md border border-[var(--ct-border)] bg-[var(--ct-bg-page)] py-0 pl-2.5 pr-7 text-[13px] text-ink-gray-9"
              @change="loadLogs()"
            >
              <option value="">{{ __('Todas as chaves') }}</option>
              <option v-for="k in data.keys" :key="k.name" :value="k.name">
                {{ k.label }}
              </option>
            </select>
            <Button
              variant="outline"
              icon-left="lucide-refresh-cw"
              :loading="loadingLogs"
              :label="__('Atualizar')"
              @click="loadLogs()"
            />
          </div>
        </div>
        <div v-if="auditLogs.length" class="overflow-x-auto">
          <table class="w-full table-fixed text-left text-[12px] leading-[17px] border-collapse">
            <thead>
              <tr class="h-[34px] border-b border-outline-gray-1 text-ink-gray-5">
                <th class="w-[140px] pr-2 font-medium">{{ __('Data/Hora') }}</th>
                <th class="w-[150px] pr-2 font-medium">{{ __('Request ID') }}</th>
                <th class="w-[120px] pr-2 font-medium">{{ __('Chave') }}</th>
                <th class="w-[280px] pr-2 font-medium">{{ __('Rota / Recurso') }}</th>
                <th class="w-20 pr-2 font-medium">{{ __('Status') }}</th>
                <th class="w-20 pr-2 font-medium">{{ __('Latência') }}</th>
                <th class="font-medium">{{ __('IP') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-1">
              <tr v-for="row in auditLogs" :key="row.name" class="h-[38px] text-ink-gray-9">
                <td class="pr-3 whitespace-nowrap">
                  {{ logTime(row.called_on) }}
                </td>
                <td class="pr-3 font-mono font-semibold">
                  {{ row.request_id || '—' }}
                </td>
                <td class="pr-3">
                  {{ row.key_label }}
                </td>
                <td class="pr-2 truncate font-mono font-semibold">
                  {{ row.route }}
                </td>
                <td class="pr-3">
                  <Badge
                    :label="String(row.status_code || 200)"
                    :theme="(row.status_code || 200) >= 400 ? 'red' : 'green'"
                    variant="subtle"
                  />
                </td>
                <td class="pr-3 whitespace-nowrap">
                  {{ row.duration_ms != null ? `${row.duration_ms} ms` : '—' }}
                </td>
                <td>
                  {{ row.ip_address || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="text-p-sm text-ink-gray-5 py-2">
          {{ __('Nenhuma chamada registrada para o filtro selecionado.') }}
        </p>
      </div>
    </div>
  </div>
  <!-- Create / edit -->
  <Dialog
    v-model:open="form.show"
    :title="form.name ? __('Edit API key') : __('New API key')"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="form.label"
          :label="__('Name')"
          :placeholder="__('e.g. ERP, website, data warehouse')"
          type="text"
        />
        <div class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">{{ __('Permissions') }}</span>
          <div
            v-for="row in SCOPE_ROWS"
            :key="row.label"
            class="flex items-center justify-between gap-4 text-p-base"
          >
            <span>{{ __(row.label) }}</span>
            <div class="flex gap-4">
              <FormControl
                v-if="row.read"
                v-model="form.scopes[row.read]"
                type="checkbox"
                :label="__('Read')"
              />
              <FormControl
                v-if="row.write"
                v-model="form.scopes[row.write]"
                type="checkbox"
                :label="__(row.writeLabel || 'Write')"
              />
            </div>
          </div>
          <FormControl
            v-model="form.scopes[ADMIN_SCOPE]"
            type="checkbox"
            :label="__('Fields and rules of the stages (admin)')"
          />
          <p v-if="form.scopes[ADMIN_SCOPE]" class="text-p-sm text-ink-amber-7">
            {{
              __(
                'The key can change which fields the chosen funnels use and the rules of each stage (visible, required, read-only).',
              )
            }}
          </p>
          <FormControl
            v-model="form.scopes[DELETE_SCOPE]"
            type="checkbox"
            :label="__('Allow DELETE of records (Cards, Contacts, Organizations, Files, Notes, Tasks)')"
          />
        </div>
        <div v-if="needsPipelines(selectedScopes)" class="flex flex-col gap-2">
          <span class="text-sm text-ink-gray-5">{{ __('Funnels') }}</span>
          <FormControl
            v-for="p in pipelines.pipelines"
            :key="p.name"
            v-model="form.pipelines[p.name]"
            type="checkbox"
            :label="p.pipeline_name"
          />
        </div>
        <FormControl
          v-model="form.allowed_ips"
          :label="__('Allowed IPs (optional)')"
          :placeholder="__('One IP address or range per line')"
          type="textarea"
        />
        <FormControl
          v-model="form.expires_on"
          :label="__('Valid until (optional)')"
          type="date"
        />
        <p v-if="confirm.rotate && confirm.rotate === form.name" class="text-p-sm text-ink-red-6">
          {{ __('The current secret stops working right away.') }}
        </p>
        <ErrorMessage :message="form.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <!-- the key list (Figma "Tabela") has no room for it: the new secret
             of a key is made here, with the same confirmation as before -->
        <Button
          v-if="form.name"
          class="mr-auto"
          :label="
            confirm.rotate === form.name
              ? __('Confirm new secret')
              : __('New secret')
          "
          :theme="confirm.rotate === form.name ? 'red' : 'gray'"
          :loading="busy === form.name + ':rotate'"
          @click="rotateFromForm"
          @blur="confirm.rotate = null"
        />
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="form.show = false"
        />
        <Button
          variant="solid"
          :label="form.name ? __('Save') : __('Create key')"
          :loading="busy === 'form'"
          @click="save"
        />
      </div>
    </template>
  </Dialog>

  <!-- The secret, once -->
  <Dialog v-model:open="secret.show" :title="__('Copy the key now')">
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">{{ secretHelp }}</p>
        <div
          class="break-all rounded bg-surface-gray-2 px-3 py-2 font-mono text-p-sm text-ink-gray-9"
        >
          {{ secret.token }}
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button
          :label="__('Copy')"
          icon-left="copy"
          @click="copyToClipboard(secret.token)"
        />
        <Button variant="solid" :label="__('Done')" @click="closeSecret" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LucideKeyRound from '~icons/lucide/key-round'
import SettingsEmptyState from '@/components/Settings/SettingsEmptyState.vue'
import SettingsPageHeader from '@/components/Settings/SettingsPageHeader.vue'
import SettingsBackLink from '@/components/Settings/SettingsBackLink.vue'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Tooltip,
  call,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { pipelinesStore } from '@/stores/pipelines'
import { copyToClipboard, timeAgo } from '@/utils'
import { apiKeys, apiKeysApi, loadApiKeys } from './apiKeysApi'
import {
  ADMIN_SCOPE,
  DELETE_SCOPE,
  SCOPE_ROWS,
  brDate,
  brDateTime,
  cleanIps,
  dayMonth,
  legacyStopped,
  needsPipelines,
  scopeSummary,
} from './apiKeysUtils'

const pipelines = pipelinesStore()
// 'keys' (the list) or 'docs' (Figma "Documentação da API")
const view = ref('keys')
const baseUrl = window.location.origin
const activeDocTab = ref('cards')
const docSections = [
  {
    id: 'cards',
    title: __('Cards e funis'),
    endpoints: [
      {
        method: 'GET',
        path: '/api/method/crm.api.pipeline.get_pipelines',
        scope: 'pipelines_read',
        desc: __('Lista todos os funis ativos da chave com suas etapas (chaves imutáveis), cores e posições.'),
        curl: `curl "${baseUrl}/api/method/crm.api.pipeline.get_pipelines" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'GET',
        path: '/api/resource/CRM Deal',
        scope: 'cards_read',
        desc: __('Lista e filtra cards nos funis autorizados da chave com paginação e ordenação.'),
        curl: `curl "${baseUrl}/api/resource/CRM%20Deal?filters=\\[\\[%22pipeline%22,%22=%22,%22<funil>%22\\]\\]&fields=\\[%22name%22,%22deal_name%22,%22organization%22,%22status%22,%22deal_value%22\\]&limit=20" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'POST',
        path: '/api/resource/CRM Deal',
        scope: 'cards_write',
        desc: __('Cria um novo card diretamente em um funil (entra na 1ª etapa se status não for informado).'),
        curl: `curl -X POST "${baseUrl}/api/resource/CRM%20Deal" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"pipeline": "<funil>", "organization": "Empresa Exemplo Ltda", "deal_value": 50000}'`,
      },
      {
        method: 'POST',
        path: '/api/method/crm.api.pipeline.move_card',
        scope: 'cards_write',
        desc: __('Move o card de etapa validando os campos obrigatórios da etapa de destino e preenchendo valores junto.'),
        curl: `curl -X POST "${baseUrl}/api/method/crm.api.pipeline.move_card" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"deal": "CRM-DEAL-2026-00001", "stage": "<etapa>", "values": {"next_step": "Enviar contrato"}}'`,
      },
    ],
  },
  {
    id: 'orgs_contacts',
    title: __('Organizações e contatos'),
    endpoints: [
      {
        method: 'POST',
        path: '/api/resource/CRM Organization',
        scope: 'organizations_write',
        desc: __('Cadastra uma organização (empresa/cedente/sacado) com CNPJ e dados cadastrais.'),
        curl: `curl -X POST "${baseUrl}/api/resource/CRM%20Organization" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"organization_name": "Acme Securitizadora S.A.", "cnpj": "11.222.333/0001-81"}'`,
      },
      {
        method: 'POST',
        path: '/api/resource/Contact',
        scope: 'contacts_write',
        desc: __('Cadastra ou atualiza um contato (sócio, decisor, financeiro) com telefone e e-mail.'),
        curl: `curl -X POST "${baseUrl}/api/resource/Contact" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"first_name": "Carlos Silva", "email_id": "carlos@acme.com.br", "mobile_no": "+5511999990000"}'`,
      },
      {
        method: 'POST',
        path: '/api/resource/CRM Lead',
        scope: 'leads_write',
        desc: __('Recebe contato de entrada (site, landing page, anúncio) e converte automaticamente em Card no funil com distribuição de responsável.'),
        curl: `curl -X POST "${baseUrl}/api/resource/CRM%20Lead" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"first_name": "Ana", "email": "ana@empresa.com.br", "mobile_no": "+5511988887777", "pipeline": "<funil>"}'`,
      },
    ],
  },
  {
    id: 'activities',
    title: __('Arquivos, notas e tarefas'),
    endpoints: [
      {
        method: 'POST',
        path: '/api/method/upload_file',
        scope: 'files_write',
        desc: __('Envia documento privado (multipart/form-data) anexado a um Card, Contato ou Organização.'),
        curl: `curl -X POST "${baseUrl}/api/method/upload_file" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -F "file=@contrato.pdf" -F "doctype=CRM Deal" -F "docname=CRM-DEAL-2026-00001" -F "is_private=1"`,
      },
      {
        method: 'POST',
        path: '/api/method/frappe.desk.form.utils.add_comment',
        scope: 'comments_write',
        desc: __('Registra um comentário na linha do tempo de um Card, Contato ou Organização.'),
        curl: `curl -X POST "${baseUrl}/api/method/frappe.desk.form.utils.add_comment" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"reference_doctype": "CRM Deal", "reference_name": "CRM-DEAL-2026-00001", "content": "Análise aprovada pelo comitê."}'`,
      },
      {
        method: 'POST',
        path: '/api/resource/FCRM Note',
        scope: 'notes_write',
        desc: __('Cria uma anotação rica vinculada ao Card (suporta HTML e fixação no topo).'),
        curl: `curl -X POST "${baseUrl}/api/resource/FCRM%20Note" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"title": "Parecer Comercial", "content": "<p>Limite aprovado: R$ 250 mil.</p>", "reference_doctype": "CRM Deal", "reference_docname": "CRM-DEAL-2026-00001"}'`,
      },
      {
        method: 'POST',
        path: '/api/resource/CRM Task',
        scope: 'tasks_write',
        desc: __('Cria tarefa comercial vinculada ao Card com prazo e responsável.'),
        curl: `curl -X POST "${baseUrl}/api/resource/CRM%20Task" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"title": "Colher assinatura digital", "due_date": "2026-11-10", "status": "Open", "reference_doctype": "CRM Deal", "reference_docname": "CRM-DEAL-2026-00001"}'`,
      },
    ],
  },
  {
    id: 'batch_sync',
    title: __('Lote e sincronização'),
    endpoints: [
      {
        method: 'POST',
        path: '/api/method/cred_hub.bulk.bulk_upsert',
        scope: 'cards_write / contacts_write / organizations_write',
        desc: __('Cria ou atualiza até 50 registros em uma única chamada HTTP com savepoint isolado por item.'),
        curl: `curl -X POST "${baseUrl}/api/method/cred_hub.bulk.bulk_upsert" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"doctype": "CRM Deal", "records": [{"pipeline": "<funil>", "organization": "Acme Ltda"}]}'`,
      },
      {
        method: 'GET',
        path: '/api/method/cred_hub.sync.get_deleted_records',
        scope: 'sync_deletes',
        desc: __('Retorna o log de registros excluídos desde um timestamp para sincronização incremental de ERPs.'),
        curl: `curl "${baseUrl}/api/method/cred_hub.sync.get_deleted_records?doctype=CRM%20Deal&since=2026-11-01%2000:00:00" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'GET',
        path: '/api/method/crm.api.forms.get_form_schema',
        scope: 'cards_read',
        desc: __('Retorna os campos visíveis, obrigatórios e somente leitura de um funil e etapa.'),
        curl: `curl "${baseUrl}/api/method/crm.api.forms.get_form_schema?doctype=CRM%20Deal&pipeline=<funil>&stage=<etapa>" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'GET',
        path: '/api/method/cred_hub.api_keys.list_records_cursor',
        scope: 'cards_read / organizations_read / contacts_read',
        desc: __('Paginação determinística por cursor (next_cursor) + filtro incremental updated_since para ERPs.'),
        curl: `curl "${baseUrl}/api/method/cred_hub.api_keys.list_records_cursor?doctype=CRM%20Deal&updated_since=2026-11-01%2000:00:00&limit=50" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
    ],
  },
  {
    id: 'credit_lookup',
    title: __('Crédito PJ'),
    endpoints: [
      {
        method: 'GET',
        path: '/api/method/cred_hub.api_keys.lookup_by_document',
        scope: 'organizations_read / cards_read / credit_read',
        desc: __('Busca 360° por CNPJ ou CPF (com ou sem máscara): retorna Organização/Contato, Cards abertos, Pasta Digital e veredito de crédito em 1 chamada.'),
        curl: `curl "${baseUrl}/api/method/cred_hub.api_keys.lookup_by_document?document=12.345.678/0001-90" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'GET',
        path: '/api/method/cred_hub.credit_check.api.get_credit_onboarding',
        scope: 'credit_read',
        desc: __('Consulta os documentos da Pasta Digital, status de conferência, Link Blindado e Relatório de Visita da empresa.'),
        curl: `curl "${baseUrl}/api/method/cred_hub.credit_check.api.get_credit_onboarding?organization=Acme%20Ltda" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>"`,
      },
      {
        method: 'POST',
        path: '/api/method/cred_hub.credit_check.api.create_onboarding_portal_link',
        scope: 'credit_write',
        desc: __('Gera (ou recupera) o link da Caixa de Correio Blindada protegido por CNPJ para enviar ao cliente.'),
        curl: `curl -X POST "${baseUrl}/api/method/cred_hub.credit_check.api.create_onboarding_portal_link" \\\n  -H "Authorization: Bearer hub_<id>_<segredo>" \\\n  -H "Content-Type: application/json" \\\n  -d '{"organization": "Acme Ltda"}'`,
      },
    ],
  },
]
const currentDocSection = computed(() =>
  docSections.find((s) => s.id === activeDocTab.value),
)
const data = computed(() => apiKeys.data)
const activeCount = computed(
  () => (data.value?.keys || []).filter((k) => k.status === 'Active').length,
)
const busy = ref(null)
const auditLogs = ref([])
const auditMetrics = ref(null)
const loadingLogs = ref(false)
const selectedLogKey = ref('')

async function loadLogs() {
  loadingLogs.value = true
  try {
    const res = await call('cred_hub.api_keys.get_api_logs', {
      api_key: selectedLogKey.value || null,
      limit: 30,
    })
    auditLogs.value = res?.logs || []
    auditMetrics.value = res?.metrics || null
  } catch (e) {
    // ignore if non-admin
  } finally {
    loadingLogs.value = false
  }
}
const confirm = reactive({ rotate: null, revoke: null })
const form = reactive({
  show: false,
  name: null,
  label: '',
  scopes: {},
  pipelines: {},
  allowed_ips: '',
  expires_on: '',
  error: '',
})
const secret = reactive({ show: false, token: '' })
// In the script: "<key>" inside the template would read as an HTML tag
const secretHelp = __(
  'This is the only time the key is shown. Store it in the system that will use it, sent as the header "Authorization: Bearer <key>".',
)

const selectedScopes = computed(() =>
  Object.keys(form.scopes).filter((s) => form.scopes[s]),
)

onMounted(() => {
  loadApiKeys()
  pipelines.ensureLoaded()
  loadLogs()
})

function pipelineLabels(names) {
  return names
    .map((n) => pipelines.getPipeline(n)?.pipeline_name || n)
    .join(', ')
}

function openForm(key = null) {
  Object.assign(form, {
    show: true,
    name: key?.name || null,
    label: key?.label || '',
    scopes: Object.fromEntries((key?.scopes || []).map((s) => [s, true])),
    pipelines: Object.fromEntries((key?.pipelines || []).map((p) => [p, true])),
    allowed_ips: key?.allowed_ips || '',
    expires_on: key?.expires_on || '',
    error: '',
  })
}

function errorText(e) {
  return (
    e?.messages?.[0] || e?.message || __('Something went wrong. Try again.')
  )
}

async function save() {
  let values = {
    label: form.label,
    scopes: selectedScopes.value,
    pipelines: needsPipelines(selectedScopes.value)
      ? Object.keys(form.pipelines).filter((p) => form.pipelines[p])
      : [],
    allowed_ips: cleanIps(form.allowed_ips),
    expires_on: form.expires_on || '',
  }
  busy.value = 'form'
  form.error = ''
  try {
    if (form.name) {
      await apiKeysApi.update(form.name, values)
      toast.success(__('Key saved'))
    } else {
      let created = await apiKeysApi.create(values)
      showSecret(created.token)
    }
    form.show = false
    await loadApiKeys()
  } catch (e) {
    form.error = errorText(e)
  } finally {
    busy.value = null
  }
}

async function rotate(key) {
  if (confirm.rotate !== key.name) {
    confirm.rotate = key.name
    return
  }
  confirm.rotate = null
  busy.value = key.name + ':rotate'
  try {
    let rotated = await apiKeysApi.rotate(key.name)
    showSecret(rotated.token)
    await loadApiKeys()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = null
  }
}

async function revoke(key) {
  if (confirm.revoke !== key.name) {
    confirm.revoke = key.name
    return
  }
  confirm.revoke = null
  busy.value = key.name + ':revoke'
  try {
    await apiKeysApi.revoke(key.name)
    toast.success(__('Key revoked'))
    await loadApiKeys()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = null
  }
}

async function rotateFromForm() {
  let key = data.value?.keys.find((k) => k.name === form.name)
  if (!key) return
  let confirmed = confirm.rotate === key.name
  await rotate(key)
  if (confirmed) form.show = false
}

// what the old key card listed, now in the tooltip of the name
function keyDetails(key) {
  return [
    __('Permissions: {0}', [scopeSummary(key.scopes)]),
    key.pipelines.length
      ? __('Funnels: {0}', [pipelineLabels(key.pipelines)])
      : null,
    key.allowed_ips
      ? __('IPs: {0}', [key.allowed_ips.split('\n').join(', ')])
      : null,
    key.expires_on ? __('Valid until {0}', [brDate(key.expires_on)]) : null,
    key.last_used_on
      ? __('Last used {0} from {1}', [
          brDateTime(key.last_used_on),
          key.last_used_ip,
        ])
      : null,
    __('Created by {0} on {1}', [key.created_by, brDate(key.created_on)]),
  ]
    .filter(Boolean)
    .join(' · ')
}

// "06/11 10:42:13" in the audit table
function logTime(value) {
  if (!value) return ''
  let [date, time = ''] = String(value).split(' ')
  let [, month, day] = date.split('-')
  return `${day}/${month} ${time.slice(0, 8)}`
}

function showSecret(token) {
  Object.assign(secret, { show: true, token })
}

function closeSecret() {
  secret.show = false
}

// However the dialog closes, the token leaves the page: it cannot be shown again
watch(
  () => secret.show,
  (open) => {
    if (!open) secret.token = ''
  },
)
</script>

<style>
/* Figma "Tabela" of the keys: Nome and Chave share the room, the dates are
   152px, 16px between cells and on the sides */
.ct-api-keys-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 152px 152px minmax(110px, auto);
  column-gap: 16px;
  padding-inline: 16px;
}
</style>
