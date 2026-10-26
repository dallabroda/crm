<template>
  <section class="flex flex-col gap-3" data-testid="pipeline-distribution">
    <h3 class="text-lg-semibold text-ink-gray-8">{{ __('Distribution') }}</h3>
    <p class="text-p-sm text-ink-gray-5">
      {{
        __(
          'Who receives the leads that arrive by themselves (ads, forms, integrations). Cards created by hand stay with whoever created them.',
        )
      }}
    </p>

    <div class="w-72">
      <FormControl
        type="select"
        :label="__('How to distribute')"
        :options="modeOptions"
        :disabled="!canManage"
        :model-value="model.mode"
        @update:model-value="(v) => (model.mode = v)"
      />
    </div>

    <!-- rules: first match wins -->
    <div v-if="model.mode === 'rules'" class="flex flex-col gap-2">
      <p class="text-p-sm text-ink-gray-5">
        {{
          __(
            'Rules are checked from top to bottom; the first one that matches decides the salesperson. Upper and lower case do not matter.',
          )
        }}
      </p>
      <div
        v-for="(rule, index) in model.rules"
        :key="index"
        class="flex items-center gap-2"
        :data-rule="index"
      >
        <span class="w-6 shrink-0 text-sm text-ink-gray-5">{{ __('If') }}</span>
        <div class="w-56">
          <FormControl
            type="select"
            :placeholder="__('Field')"
            :options="fieldOptions"
            :disabled="!canManage"
            :model-value="rule.field || null"
            @update:model-value="(v) => (rule.field = v)"
          />
        </div>
        <span class="shrink-0 text-sm text-ink-gray-5">{{ __('is') }}</span>
        <div class="w-48">
          <FormControl
            type="text"
            :placeholder="__('Value')"
            :disabled="!canManage"
            :model-value="rule.value"
            @update:model-value="(v) => (rule.value = v)"
          />
        </div>
        <span class="shrink-0 text-sm text-ink-gray-5">→</span>
        <div class="w-56">
          <FormControl
            type="select"
            :placeholder="__('Salesperson')"
            :options="salespeopleOptions"
            :disabled="!canManage"
            :model-value="rule.user || null"
            @update:model-value="(v) => (rule.user = v)"
          />
        </div>
        <Button
          v-if="canManage"
          variant="ghost"
          icon="lucide-x"
          :tooltip="__('Remove rule')"
          :aria-label="__('Remove rule')"
          @click="model.rules.splice(index, 1)"
        />
      </div>
      <div v-if="canManage">
        <Button
          :label="__('Add rule')"
          icon-left="lucide-plus"
          @click="model.rules.push({ field: '', value: '', user: '' })"
        />
      </div>
      <div class="w-72">
        <FormControl
          type="select"
          :label="__('When no rule matches')"
          :options="fallbackOptions"
          :disabled="!canManage"
          :model-value="model.fallback"
          @update:model-value="(v) => (model.fallback = v)"
        />
      </div>
    </div>

    <!-- who takes part in the round robin (rodízio) -->
    <div
      v-if="model.mode === 'round_robin' || model.fallback === 'round_robin'"
      class="flex flex-col gap-1"
    >
      <div class="text-sm text-ink-gray-7">
        {{ __('Salespeople in the round robin') }}
      </div>
      <p v-if="!members.length" class="text-p-sm text-ink-gray-5">
        {{ __('Add members to the funnel to distribute its leads.') }}
      </p>
      <label
        v-for="member in members"
        :key="member.user"
        class="flex items-center gap-2 text-sm text-ink-gray-8"
      >
        <Checkbox
          :model-value="inRoundRobin(member.user)"
          :disabled="!canManage"
          @update:model-value="(v) => setRoundRobin(member.user, v)"
        />
        {{ userName(member.user) }}
      </label>
    </div>

    <p class="text-p-sm text-ink-gray-5">
      {{
        __(
          'A salesperson who left the funnel is skipped. A lead whose e-mail or phone already has an open card in this funnel does not create another card: it is added to that card and its owner is notified.',
        )
      }}
    </p>
  </section>
</template>

<script setup>
// Distribution of the leads that reach a funnel by themselves (credtech#51):
// { mode: 'round_robin' | 'rules', round_robin_users: [user] (empty = the
//   salespeople), rules: [{ field, value, user }], fallback: 'round_robin' | 'owner' }
import { Button, Checkbox, FormControl } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  members: { type: Array, required: true },
  // card fields that rules can test: [{ label, value }]
  fieldOptions: { type: Array, required: true },
  canManage: { type: Boolean, default: false },
  userName: { type: Function, required: true },
})

const model = defineModel({ type: Object, required: true })

const modeOptions = [
  { label: __('Round robin among salespeople'), value: 'round_robin' },
  { label: __('By rules'), value: 'rules' },
]
const fallbackOptions = [
  { label: __('Round robin among salespeople'), value: 'round_robin' },
  { label: __('Funnel owner'), value: 'owner' },
]

const salespeopleOptions = computed(() =>
  props.members.map((m) => ({ label: props.userName(m.user), value: m.user })),
)

// An empty list means the funnel's salespeople (its owners when it has none),
// as the server reads it
const defaultRoundRobin = computed(() => {
  let salespeople = props.members.filter((m) => m.role === 'Member')
  return (salespeople.length ? salespeople : props.members).map((m) => m.user)
})

function inRoundRobin(user) {
  let users = model.value.round_robin_users || []
  return (users.length ? users : defaultRoundRobin.value).includes(user)
}

function setRoundRobin(user, enabled) {
  let users = model.value.round_robin_users?.length
    ? [...model.value.round_robin_users]
    : [...defaultRoundRobin.value]
  // at least one salesperson stays in (an empty list would mean everyone)
  if (!enabled && users.length === 1 && users[0] === user) return
  users = enabled
    ? [...new Set([...users, user])]
    : users.filter((u) => u !== user)
  // back to the default set: keep it empty, so new salespeople join too
  let sameAsDefault =
    users.length === defaultRoundRobin.value.length &&
    users.every((u) => defaultRoundRobin.value.includes(u))
  model.value.round_robin_users = sameAsDefault ? [] : users
}
</script>
