import { describe, it, expect } from 'vitest'
import {
  automationFlowDoc,
} from '@/components/Settings/WorkflowAutomations/newAutomation'

const base = { title: 'Tarefa', stage: '', then: 'task', taskTitle: 'T' }

describe('automationFlowDoc', () => {
  it('turns a stage change into a status change to that stage', () => {
    const doc = automationFlowDoc({ ...base, when: 'stage', stage: 'Proposta' })
    expect(doc.trigger_type).toBe('Field Value Changed')
    expect(doc.trigger_field).toBe('status')
    expect(doc.to_value).toBe('Proposta')
    expect(doc.filters).toBe('[]')
    expect(doc.enabled).toBe(0)
  })

  it('filters the card on the stage for the other triggers', () => {
    const doc = automationFlowDoc({ ...base, when: 'created', stage: 'X' })
    expect(doc.trigger_type).toBe('Doc Created')
    expect(doc.to_value).toBe('')
    expect(JSON.parse(doc.filters)).toEqual([['status', '=', 'X']])
  })

  it('creates the owner task, or leaves the steps to the editor', () => {
    const task = automationFlowDoc({ ...base, when: 'stage' }).actions
    expect(task).toHaveLength(1)
    const params = JSON.parse(task[0].params)
    expect(task[0].action_type).toBe('CreateDocument')
    expect(params.doctype).toBe('CRM Task')
    expect(params.values.assigned_to).toContain('deal_owner')
    expect(
      automationFlowDoc({ ...base, when: 'manual', then: 'editor' }).actions,
    ).toEqual([])
  })
})
