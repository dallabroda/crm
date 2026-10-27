const frappeRequest = vi.fn()

vi.mock('frappe-ui', () => ({ call: vi.fn(), frappeRequest }))

const {
  plan,
  loadPlan,
  usage,
  describeChange,
  chosenExtras,
  overLimitAfter,
  inGrace,
  statusBadge,
  dayAfterTrial,
} = await import('@/components/Settings/UsersAndPlan/planApi')

// Shape of cred_hub.billing.get_plan with billing on
function planData(values = {}) {
  return {
    enabled: true,
    limit: 2,
    free: 2,
    extras: 0,
    pending_extras: 0,
    scheduled_extras: null,
    scheduled_from: null,
    upgrade: null,
    grace_until: null,
    used_active: 2,
    used_invited: 0,
    status: 'Free',
    next_due: null,
    amount: 0,
    price_per_user: 60,
    currency: 'BRL',
    invoice_url: null,
    paused_users: [],
    unlimited: false,
    needs_payer: true,
    payer: null,
    ...values,
  }
}

const active = (values = {}) =>
  planData({
    status: 'Active',
    extras: 3,
    limit: 5,
    next_due: '2026-11-10',
    amount: 180,
    needs_payer: false,
    ...values,
  })

describe('loadPlan', () => {
  beforeEach(() => {
    frappeRequest.mockReset()
  })

  it('shows the page while billing is on', async () => {
    frappeRequest.mockResolvedValue(planData())
    await loadPlan()
    expect(plan.enabled).toBe(true)
    expect(plan.data.free).toBe(2)
  })

  it('hides the page while billing is off', async () => {
    frappeRequest.mockResolvedValue({ enabled: false })
    await loadPlan()
    expect(plan.enabled).toBe(false)
    expect(plan.data).toBe(null)
  })

  it('hides the page without the cred_hub app or for non-admins', async () => {
    frappeRequest.mockRejectedValue(new Error('not allowed'))
    await loadPlan()
    expect(plan.enabled).toBe(false)
    expect(plan.loading).toBe(false)
  })
})

describe('usage', () => {
  it('counts pending invitations as used seats', () => {
    expect(usage(planData({ used_active: 1, used_invited: 1 }))).toEqual({
      used: 2,
      limit: 2,
      unlimited: false,
      full: true,
    })
  })

  it('is never full without a limit', () => {
    expect(usage(planData({ unlimited: true, used_active: 9 })).full).toBe(
      false,
    )
  })
})

describe('chosenExtras', () => {
  it('is the first subscription waiting for payment', () => {
    expect(
      chosenExtras(planData({ status: 'Awaiting Payment', pending_extras: 2 })),
    ).toBe(2)
  })

  it('is the scheduled decrease, including canceling to 0', () => {
    expect(chosenExtras(active({ scheduled_extras: 1 }))).toBe(1)
    expect(chosenExtras(active({ scheduled_extras: 0 }))).toBe(0)
  })

  it('is the upgrade still unpaid', () => {
    const upgrade = { extras: 5, paid_extras: 3, overdue: true }
    expect(chosenExtras(active({ extras: 3, upgrade }))).toBe(5)
  })

  it('ignores seats contracted before going back to free', () => {
    expect(chosenExtras(planData({ status: 'Free', extras: 4 }))).toBe(0)
  })
})

describe('describeChange', () => {
  it('does nothing when the quantity does not change', () => {
    expect(describeChange(active(), 3).kind).toBe('same')
    expect(describeChange(planData(), 0).kind).toBe('same')
  })

  it('subscribes when there is no active subscription', () => {
    expect(describeChange(planData(), 2)).toEqual({
      kind: 'subscribe',
      monthly: 120,
    })
    expect(describeChange(planData({ status: 'Canceled' }), 1).kind).toBe(
      'subscribe',
    )
  })

  it('goes back to free from a subscription not paid yet', () => {
    const awaiting = planData({ status: 'Awaiting Payment', pending_extras: 2 })
    expect(describeChange(awaiting, 0).kind).toBe('free')
  })

  it('increases, decreases and cancels an active subscription', () => {
    expect(describeChange(active(), 4)).toEqual({
      kind: 'increase',
      monthly: 240,
    })
    expect(describeChange(active(), 1).kind).toBe('decrease')
    expect(describeChange(active(), 0).kind).toBe('cancel')
  })

  it('keeps what is paid, dropping a scheduled decrease or an unpaid upgrade', () => {
    expect(describeChange(active({ scheduled_extras: 1 }), 3).kind).toBe('keep')
    const upgrade = { extras: 5, paid_extras: 3, overdue: false }
    expect(describeChange(active({ extras: 5, upgrade }), 3).kind).toBe('keep')
    // a smaller upgrade still counts from what is paid
    expect(describeChange(active({ extras: 5, upgrade }), 4).kind).toBe(
      'increase',
    )
  })

  it('treats an empty or negative quantity as 0', () => {
    expect(describeChange(active(), '').kind).toBe('cancel')
    expect(describeChange(active(), -2).kind).toBe('cancel')
  })
})

describe('overLimitAfter', () => {
  it('counts who is paused by a smaller plan', () => {
    expect(overLimitAfter(active({ used_active: 5 }), 1)).toBe(2)
    expect(overLimitAfter(active({ used_active: 3 }), 1)).toBe(0)
  })

  it('does not count pending invitations, which are not paused', () => {
    expect(overLimitAfter(active({ used_active: 5, used_invited: 2 }), 1)).toBe(
      2,
    )
    expect(overLimitAfter(active({ used_active: 2, used_invited: 3 }), 0)).toBe(
      0,
    )
  })
})

describe('inGrace', () => {
  it('lasts until the end of the grace day', () => {
    const late = planData({ status: 'Past Due', grace_until: '2026-10-30' })
    expect(inGrace(late, '2026-10-30')).toBe(true)
    expect(inGrace(late, '2026-10-31')).toBe(false)
    expect(inGrace(planData(), '2026-10-30')).toBe(false)
  })
})

describe('statusBadge', () => {
  it('names every status of the plan', () => {
    expect(statusBadge('Past Due')).toEqual({
      label: 'Payment overdue',
      theme: 'red',
    })
    expect(statusBadge('Awaiting Payment').theme).toBe('orange')
  })
})

describe('free trial', () => {
  it('has no limit and is not full during the trial', () => {
    const data = planData({ in_trial: true, limit: 1000000, used_active: 7 })
    expect(usage(data)).toMatchObject({ used: 7, unlimited: true, full: false })
  })

  it('shows the trial instead of the free plan', () => {
    expect(statusBadge('Free', true).label).toBe('Free trial')
    expect(statusBadge('Free', false).label).toBe('Free plan')
    expect(statusBadge('Awaiting Payment', true).label).toBe('Awaiting payment')
  })

  it('knows the day after the trial, across months and years', () => {
    expect(dayAfterTrial(planData({ trial_ends_on: '2026-11-09' }))).toBe(
      '2026-11-10',
    )
    expect(dayAfterTrial(planData({ trial_ends_on: '2026-10-31' }))).toBe(
      '2026-11-01',
    )
    expect(dayAfterTrial(planData({ trial_ends_on: '2026-12-31' }))).toBe(
      '2027-01-01',
    )
    expect(dayAfterTrial(planData())).toBeNull()
  })
})
