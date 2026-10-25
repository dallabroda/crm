<template>
  <Dialog v-model:open="show" :size="'sm'" bare>
    <template #default>
      <div class="p-4 pt-5">
        <div class="flex justify-center">
          <div class="flex flex-col items-center">
            <CRMLogo class="mb-3 size-12" />
            <Dialog.Title as-child>
              <h3 class="text-2xl-semibold text-ink-gray-9">Cred Hub</h3>
            </Dialog.Title>
          </div>
        </div>
        <hr class="border-t my-3 mx-2" />
        <div>
          <a
            v-for="link in links"
            :key="link.label"
            class="flex py-2 px-2 hover:bg-surface-gray-1 rounded-4 cursor-pointer"
            target="_blank"
            :href="link.url"
          >
            <component
              :is="link.icon"
              v-if="link.icon"
              class="size-4 mr-2 text-ink-gray-7"
            />
            <span class="text-base text-ink-gray-8">
              {{ link.label }}
            </span>
          </a>
        </div>
        <hr class="border-t my-3 mx-2" />
        <!-- AGPL-3.0: users of the service get a link to the source of the
             running version; original copyright notices stay in the code -->
        <p class="text-sm text-ink-gray-6 px-2 mt-2">
          © CredTech Digital.
          {{
            __(
              'Free software under the AGPL-3.0 license, built on open source projects (credits in the source code).',
            )
          }}
        </p>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import GitHubIcon from '@/components/Icons/GitHubIcon.vue'
import LucideGlobe from '~icons/lucide/globe'
import { Dialog } from 'frappe-ui'

let show = defineModel({ type: Boolean })

let links = [
  {
    label: __('Website'),
    url: 'https://credtechdigital.com.br',
    icon: LucideGlobe,
  },
  {
    label: __('Source code (AGPL-3.0)'),
    url: 'https://github.com/dallabroda/crm',
    icon: GitHubIcon,
  },
]
</script>
