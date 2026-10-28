<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex px-2 justify-between">
      <div class="flex flex-col gap-1 w-9/12">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Invite users') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Invite people by e-mail and choose what each one can do. Access to the company is only by invitation.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Send Invites')"
          variant="solid"
          :disabled="
            !invitees.length || userExistMessage || inviteeExistMessage
          "
          :loading="inviteByEmail.loading"
          @click="inviteByEmail.submit()"
        />
      </div>
    </div>
    <div class="flex-1 flex flex-col px-2 gap-8 overflow-y-auto">
      <div>
        <FormControl
          type="textarea"
          :label="__('Invite By Email')"
          placeholder="user1@example.com, user2@example.com, ..."
          :debounce="100"
          :disabled="inviteByEmail.loading"
          :description="
            __(
              'You can invite multiple users by comma separating their email addresses',
            )
          "
          @input="updateInvitees($event.target.value)"
        />
        <div
          v-if="userExistMessage || inviteeExistMessage"
          class="text-xs text-ink-red-5 mt-1.5"
        >
          {{ userExistMessage || inviteeExistMessage }}
        </div>
        <FormControl
          v-model="role"
          type="select"
          class="mt-4"
          :label="__('Invite As')"
          :options="roleOptions"
          :description="description"
        />
      </div>
      <template v-if="pendingInvitations.data?.length && !invitees.length">
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between text-base-semibold">
            <div>{{ __('Invitations not accepted yet') }}</div>
          </div>
          <ul class="flex flex-col gap-1">
            <li
              v-for="invite in pendingInvitations.data"
              :key="invite.name"
              class="flex items-center justify-between gap-3 px-3 py-2 rounded-6 bg-surface-gray-2"
            >
              <div class="flex min-w-0 flex-col gap-0.5">
                <div class="text-base">
                  <span class="text-ink-gray-8">{{ invite.email }}</span>
                  <span class="text-ink-gray-5">
                    ({{ roleMap[invite.role] }})
                  </span>
                </div>
                <div class="text-p-sm text-ink-gray-5">
                  {{
                    invite.invited_by_name
                      ? __('Invited by {0} on {1}', [
                          invite.invited_by_name,
                          date(invite.sent_on),
                        ])
                      : __('Sent on {0}', [date(invite.sent_on)])
                  }}
                  ·
                  <span v-if="invite.expired" class="text-ink-red-4">
                    {{ __('Expired on {0}', [date(invite.valid_until)]) }}
                  </span>
                  <span v-else>
                    {{ __('Valid until {0}', [date(invite.valid_until)]) }}
                  </span>
                </div>
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button
                  :label="__('Resend')"
                  icon-left="lucide-send"
                  size="sm"
                  :loading="resending === invite.name"
                  @click="resend(invite)"
                />
                <Button
                  :tooltip="__('Cancel invitation')"
                  icon="lucide-x"
                  variant="ghost"
                  @click="toCancel = invite"
                />
              </div>
            </li>
          </ul>
        </div>
      </template>
    </div>
    <Dialog
      :open="Boolean(toCancel)"
      :title="__('Cancel invitation?')"
      :actions="[
        {
          label: __('Cancel invitation'),
          variant: 'solid',
          theme: 'red',
          loading: canceling,
          onClick: cancelInvitation,
        },
      ]"
      @update:open="(open) => !open && (toCancel = null)"
    >
      <template #default>
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              '{0} will no longer be able to use the invitation link. You can invite them again later.',
              [toCancel?.email],
            )
          }}
        </p>
      </template>
    </Dialog>
    <div class="flex items-center gap-3">
      <ErrorMessage :message="error" />
      <Button
        v-if="limitReached && isAdmin()"
        class="shrink-0"
        :label="__('Open Users and Plan')"
        @click="activeSettingsPage = __('Users and Plan')"
      />
    </div>
  </div>
</template>
<script setup>
import { validateEmail, convertArrayToString, formatDate } from '@/utils'
import { usersStore } from '@/stores/users'
import { useTelemetry } from '@framework/ui/telemetry'
import { useCrmOnboarding } from '@/composables/onboarding'
import { activeSettingsPage } from '@/composables/settings'
import { toast, call, createResource, Dialog, FormControl } from 'frappe-ui'
import { ref, computed } from 'vue'

const { completeStep } = useCrmOnboarding()
const { users, isAdmin } = usersStore()
const { capture } = useTelemetry()

const invitees = ref([])
const role = ref('Sales User')
const error = ref(null)
// No seat left in the Cred Hub plan (credtech#25)
const limitReached = ref(false)

const userExistMessage = computed(() => {
  const inviteesSet = new Set(invitees.value)
  if (!inviteesSet.size) return null

  if (!users.data?.crmUsers?.length) return null
  const existingEmails = users.data.crmUsers.map((user) => user.name)
  const existingUsersSet = new Set(existingEmails)

  const existingInvitees = inviteesSet.intersection(existingUsersSet)
  if (existingInvitees.size === 0) return null

  return __('User with email {0} already exists', [
    Array.from(existingInvitees).join(', '),
  ])
})

const inviteeExistMessage = computed(() => {
  const inviteesSet = new Set(invitees.value)
  if (!inviteesSet.size) return null

  if (!pendingInvitations.data?.length) return null
  // an expired invitation does not block a new one: inviting again replaces it
  const existingEmails = pendingInvitations.data
    .filter((invite) => !invite.expired)
    .map((invite) => invite.email)
  const existingUsersSet = new Set(existingEmails)

  const existingInvitees = inviteesSet.intersection(existingUsersSet)
  if (existingInvitees.size === 0) return null

  return __('User with email {0} already invited', [
    Array.from(existingInvitees).join(', '),
  ])
})

const description = computed(() => {
  return {
    'System Manager': __(
      'Can manage everything in the CRM, including users, plan, customizations and settings.',
    ),
    'Sales Manager': __(
      'Can invite and manage salespeople and create views (reports) for the whole team.',
    ),
    'Sales User': __(
      'Works with the cards of their funnels and creates their own views (reports).',
    ),
  }[role.value]
})

const roleOptions = computed(() => {
  return [
    { value: 'Sales User', label: __('Sales User') },
    ...(isAdmin() ? [{ value: 'Sales Manager', label: __('Manager') }] : []),
    ...(isAdmin() ? [{ value: 'System Manager', label: __('Admin') }] : []),
  ]
})

const roleMap = {
  'Sales User': __('Sales User'),
  'Sales Manager': __('Manager'),
  'System Manager': __('Admin'),
}

const inviteByEmail = createResource({
  url: 'crm.api.invite_by_email',
  makeParams() {
    return {
      emails: convertArrayToString(invitees.value),
      role: role.value,
    }
  },
  onSuccess() {
    role.value = 'Sales User'
    error.value = null
    limitReached.value = false
    invitees.value = []
    pendingInvitations.reload()
    toast.success(__('Invitations sent successfully'))
    completeStep('invite_your_team')
    capture('user_invited')
  },
  onError(err) {
    error.value = err?.messages?.[0]
    limitReached.value = err?.exc_type === 'UserLimitError'
    toast.error(error.value)
  },
})

// Invitations not accepted yet, pending or expired, with dates and who invited
const INVITATIONS = 'crm.fcrm.doctype.crm_invitation.crm_invitation.'
const pendingInvitations = createResource({
  url: INVITATIONS + 'get_invitations',
  auto: true,
})

const resending = ref(null)
async function resend(invite) {
  resending.value = invite.name
  try {
    await call(INVITATIONS + 'resend_invitation', { name: invite.name })
    toast.success(__('Invitation sent again to {0}', [invite.email]))
    pendingInvitations.reload()
  } catch (e) {
    error.value = e?.messages?.[0] || __('Something went wrong')
    limitReached.value = e?.exc_type === 'UserLimitError'
    toast.error(error.value)
  } finally {
    resending.value = null
  }
}

const toCancel = ref(null)
const canceling = ref(false)
async function cancelInvitation() {
  canceling.value = true
  try {
    await call('frappe.client.delete', {
      doctype: 'CRM Invitation',
      name: toCancel.value.name,
    })
    toast.success(__('Invitation canceled'))
    toCancel.value = null
    pendingInvitations.reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Something went wrong'))
  } finally {
    canceling.value = false
  }
}

// "9 nov 2026" in Portuguese, "Nov 9, 2026" in English
function date(value) {
  return formatDate(value, 'MMM D, YYYY')
}

function updateInvitees(value) {
  const emails = value
    .split(',')
    .map((email) => email.trim())
    .filter((email) => validateEmail(email))
  invitees.value = emails
}
</script>
