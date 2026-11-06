<template>
  <div class="flex h-full flex-col gap-6 text-ink-gray-8">
    <SettingsPageHeader :title="__('API')">
      <template #description>
        {{
          __(
            'Keys for other systems to read and write your cards, contacts and organizations. Each key only reaches the funnels you choose and does not take a user seat.',
          )
        }}
      </template>
      <template #actions>
        <div class="flex items-center gap-2">
          <a
            href="/api-docs"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex h-7 items-center gap-1.5 rounded border border-outline-gray-2 bg-surface-white px-2.5 text-sm font-medium text-ink-gray-8 hover:bg-surface-gray-2"
          >
            <span>{{ __('Documentação da API ↗') }}</span>
          </a>
          <Button
            v-if="data"
            variant="solid"
            icon-left="plus"
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

    <div v-else class="flex flex-col gap-4 overflow-y-auto">
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

      <div
        v-for="key in data.keys"
        :key="key.name"
        class="flex flex-col gap-2 rounded border border-outline-gray-1 p-4"
        :class="{ 'opacity-60': key.status !== 'Active' }"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex flex-col gap-0.5">
            <div class="flex items-center gap-2">
              <span class="text-base-semibold text-ink-gray-9">
                {{ key.label }}
              </span>
              <Badge
                :label="key.status === 'Active' ? __('In use') : __('Revoked')"
                :theme="key.status === 'Active' ? 'green' : 'gray'"
                variant="subtle"
              />
            </div>
            <span class="font-mono text-p-sm text-ink-gray-6">
              {{ key.prefix }}_…{{ key.secret_hint }}
            </span>
          </div>
          <div v-if="key.status === 'Active'" class="flex gap-2">
            <Button :label="__('Edit')" @click="openForm(key)" />
            <Button
              :label="
                confirm.rotate === key.name
                  ? __('Confirm new secret')
                  : __('New secret')
              "
              :theme="confirm.rotate === key.name ? 'red' : 'gray'"
              :loading="busy === key.name + ':rotate'"
              @click="rotate(key)"
              @blur="confirm.rotate = null"
            />
            <Button
              :label="
                confirm.revoke === key.name
                  ? __('Confirm revoke')
                  : __('Revoke')
              "
              :theme="confirm.revoke === key.name ? 'red' : 'gray'"
              :loading="busy === key.name + ':revoke'"
              @click="revoke(key)"
              @blur="confirm.revoke = null"
            />
          </div>
        </div>
        <p v-if="confirm.rotate === key.name" class="text-p-sm text-ink-red-6">
          {{ __('The current secret stops working right away.') }}
        </p>
        <p v-if="confirm.revoke === key.name" class="text-p-sm text-ink-red-6">
          {{ __('The key stops working right away. This cannot be undone.') }}
        </p>
        <div class="flex flex-wrap gap-x-6 gap-y-1 text-p-sm text-ink-gray-6">
          <span>{{ __('Permissions: {0}', [scopeSummary(key.scopes)]) }}</span>
          <span v-if="key.pipelines.length">
            {{ __('Funnels: {0}', [pipelineLabels(key.pipelines)]) }}
          </span>
          <span v-if="key.allowed_ips">
            {{ __('IPs: {0}', [key.allowed_ips.split('\n').join(', ')]) }}
          </span>
          <span v-if="key.expires_on">
            {{ __('Valid until {0}', [brDate(key.expires_on)]) }}
          </span>
          <span>
            {{
              key.last_used_on
                ? __('Last used {0} from {1}', [
                    brDateTime(key.last_used_on),
                    key.last_used_ip,
                  ])
                : __('Never used')
            }}
          </span>
          <span>
            {{
              __('Created by {0} on {1}', [
                key.created_by,
                brDate(key.created_on),
              ])
            }}
          </span>
        </div>
      </div>

      <!-- Gold-Standard API Documentation & Reference Section -->
      <div class="mt-4 flex flex-col gap-4 rounded-lg border border-outline-gray-1 bg-surface-gray-1 p-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="flex flex-col gap-1">
            <div class="flex items-center gap-2">
              <span class="text-lg font-semibold text-ink-gray-9">
                {{ __('Documentação e Referência Rápida da API REST') }}
              </span>
              <Badge :label="__('Padrão Ouro · v1')" theme="blue" variant="subtle" />
            </div>
            <p class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'Integre seu ERP, site, motor de crédito ou data warehouse com autenticação Bearer, isolamento por funil, operações em lote (Batch) e sincronização incremental.',
                )
              }}
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <a
              href="/api/method/cred_hub.api_keys.get_openapi_spec"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 rounded bg-surface-white px-3 py-1.5 text-sm font-medium text-ink-gray-8 border border-outline-gray-2 hover:bg-surface-gray-2"
            >
              <span>{{ __('OpenAPI 3.1 (JSON) ↗') }}</span>
            </a>
            <a
              href="/api-docs"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 rounded bg-surface-white px-3 py-1.5 text-sm font-medium text-[color:var(--ct-accent-text)] border border-outline-gray-2 hover:bg-surface-gray-2"
            >
              <span>{{ __('Abrir Documentação & Playground (/api-docs) ↗') }}</span>
            </a>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-p-sm">
          <div class="rounded border border-outline-gray-1 bg-surface-white p-3">
            <div class="text-xs font-medium uppercase text-ink-gray-5">
              {{ __('URL Base') }}
            </div>
            <div class="mt-1 flex items-center justify-between gap-2">
              <code class="truncate font-mono text-xs text-ink-gray-9">{{ baseUrl }}</code>
              <Button
                size="sm"
                variant="ghost"
                icon="copy"
                @click="copyToClipboard(baseUrl)"
              />
            </div>
          </div>
          <div class="rounded border border-outline-gray-1 bg-surface-white p-3">
            <div class="text-xs font-medium uppercase text-ink-gray-5">
              {{ __('Cabeçalho de Autenticação') }}
            </div>
            <div class="mt-1 font-mono text-xs text-ink-gray-9 truncate">
              Authorization: Bearer hub_&lt;id&gt;_&lt;segredo&gt;
            </div>
          </div>
          <div class="rounded border border-outline-gray-1 bg-surface-white p-3">
            <div class="text-xs font-medium uppercase text-ink-gray-5">
              {{ __('Rate Limit (Janela Deslizante)') }}
            </div>
            <div class="mt-1 text-xs text-ink-gray-8">
              {{ __('300 chamadas/min (leitura) · 60 escritas/min por chave') }}
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-2 border-b border-outline-gray-1 pb-2">
          <button
            v-for="section in docSections"
            :key="section.id"
            type="button"
            class="rounded px-3 py-1 text-sm font-medium transition-colors"
            :class="
              activeDocTab === section.id
                ? 'bg-ink-gray-9 text-surface-white'
                : 'bg-surface-white text-ink-gray-7 hover:bg-surface-gray-2 border border-outline-gray-1'
            "
            @click="activeDocTab = section.id"
          >
            {{ section.title }}
          </button>
        </div>

        <div v-if="currentDocSection" class="flex flex-col gap-3">
          <div
            v-for="ep in currentDocSection.endpoints"
            :key="ep.path"
            class="rounded border border-outline-gray-1 bg-surface-white p-3.5 flex flex-col gap-2"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <Badge
                  :label="ep.method"
                  :theme="ep.method === 'GET' ? 'blue' : ep.method === 'DELETE' ? 'red' : 'green'"
                  variant="subtle"
                />
                <code class="font-mono text-xs font-semibold text-ink-gray-9">{{ ep.path }}</code>
              </div>
              <span class="text-xs text-ink-gray-5">
                {{ __('Escopo:') }} <code class="font-mono">{{ ep.scope }}</code>
              </span>
            </div>
            <p class="text-p-sm text-ink-gray-7">{{ ep.desc }}</p>
            <div
              v-if="ep.curl"
              class="relative rounded bg-surface-gray-2 p-2.5 font-mono text-xs text-ink-gray-9 overflow-x-auto whitespace-pre"
            >{{ ep.curl }}</div>
          </div>
        </div>
      </div>

      <!-- Live API Audit & Telemetry Logs -->
      <div class="mt-2 flex flex-col gap-3 rounded-lg border border-outline-gray-1 bg-surface-white p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-lg font-semibold text-ink-gray-9">
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
            <p class="text-p-xs text-ink-gray-6 mt-0.5">
              {{
                __(
                  'Histórico em tempo real das requisições autenticadas por chave (com Request ID, status HTTP, tempo de resposta e IP de origem).',
                )
              }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <select
              v-model="selectedLogKey"
              class="h-7 rounded border border-outline-gray-2 bg-surface-white px-2 text-xs text-ink-gray-8"
              @change="loadLogs()"
            >
              <option value="">{{ __('Todas as chaves') }}</option>
              <option v-for="k in data.keys" :key="k.name" :value="k.name">
                {{ k.label }}
              </option>
            </select>
            <Button
              size="sm"
              variant="outline"
              :loading="loadingLogs"
              :label="__('Atualizar')"
              @click="loadLogs()"
            />
          </div>
        </div>

        <div v-if="auditLogs.length" class="overflow-x-auto">
          <table class="w-full text-left text-xs border-collapse">
            <thead>
              <tr class="border-b border-outline-gray-1 text-ink-gray-5">
                <th class="py-2 pr-3 font-medium">{{ __('Data/Hora') }}</th>
                <th class="py-2 pr-3 font-medium">{{ __('Request ID') }}</th>
                <th class="py-2 pr-3 font-medium">{{ __('Chave') }}</th>
                <th class="py-2 pr-3 font-medium">{{ __('Rota / Recurso') }}</th>
                <th class="py-2 pr-3 font-medium">{{ __('Status') }}</th>
                <th class="py-2 pr-3 font-medium">{{ __('Latência') }}</th>
                <th class="py-2 font-medium">{{ __('IP') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-1">
              <tr v-for="row in auditLogs" :key="row.name" class="text-ink-gray-8">
                <td class="py-2 pr-3 whitespace-nowrap text-ink-gray-6">
                  {{ brDateTime(row.called_on) }}
                </td>
                <td class="py-2 pr-3 font-mono text-[11px] text-ink-gray-6">
                  {{ row.request_id || '—' }}
                </td>
                <td class="py-2 pr-3 font-medium">
                  {{ row.key_label }}
                </td>
                <td class="py-2 pr-3 font-mono text-[11px]">
                  {{ row.route }}
                </td>
                <td class="py-2 pr-3">
                  <Badge
                    :label="String(row.status_code || 200)"
                    :theme="(row.status_code || 200) >= 400 ? 'red' : 'green'"
                    variant="subtle"
                  />
                </td>
                <td class="py-2 pr-3 whitespace-nowrap text-ink-gray-6">
                  {{ row.duration_ms != null ? `${row.duration_ms} ms` : '—' }}
                </td>
                <td class="py-2 font-mono text-[11px] text-ink-gray-6">
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
        <ErrorMessage :message="form.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
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
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { pipelinesStore } from '@/stores/pipelines'
import { copyToClipboard } from '@/utils'
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
const baseUrl = window.location.origin
const activeDocTab = ref('cards')
const docSections = [
  {
    id: 'cards',
    title: __('Cards (Deals) & Funis'),
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
    title: __('Organizações, Contatos & Entrada'),
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
    title: __('Arquivos, Notas, Comentários & Tarefas'),
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
    title: __('Lote (Batch API), Sync & Schema'),
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
    title: __('Crédito PJ, Pasta Digital & Busca 360°'),
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
