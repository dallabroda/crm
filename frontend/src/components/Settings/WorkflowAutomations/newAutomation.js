// The Automation Flow the "Nova automação" modal creates (Figma 2424:24682):
// a draft on the card, with the builder's defaults, that the builder opens
// right after. Same shapes as the builder saves and as crm.automation.
// reference_flows writes.

const TRIGGERS = {
  // a stage change is a change of the card's status (CRM Deal Status)
  stage: { trigger_type: 'Field Value Changed', trigger_field: 'status' },
  created: { trigger_type: 'Doc Created' },
  updated: { trigger_type: 'Doc Updated' },
  manual: { trigger_type: 'Manual' },
}

export function automationFlowDoc({ title, when, stage, then, taskTitle }) {
  const trigger = TRIGGERS[when] || TRIGGERS.stage
  const onStageChange = trigger.trigger_type === 'Field Value Changed'
  return {
    doctype: 'Automation Flow',
    title,
    document_type: 'CRM Deal',
    // a draft: it runs once someone turns it on in the builder
    enabled: 0,
    trigger_type: trigger.trigger_type,
    trigger_field: trigger.trigger_field || '',
    from_value: '',
    // "Se Etapa = X": the stage it moves to, or a filter on the card
    to_value: onStageChange ? stage || '' : '',
    filters: JSON.stringify(
      !onStageChange && stage ? [['status', '=', stage]] : [],
    ),
    condition: '',
    relationships: '[]',
    run_as: 'Automation User',
    automation_user: '',
    stop_on_error: 1,
    throttle_per_minute: 0,
    actions: then === 'task' ? [ownerTaskStep(taskTitle)] : [],
  }
}

// "Criar tarefa para o responsável": a to-do on the card for its owner, due
// the next day
function ownerTaskStep(taskTitle) {
  return {
    doctype: 'Automation Action',
    idx: 1,
    step_key: 'create_task',
    step_type: 'Action',
    action_type: 'CreateDocument',
    target: 'trigger',
    params: JSON.stringify({
      doctype: 'CRM Task',
      values: {
        title: taskTitle,
        status: 'Todo',
        priority: 'Medium',
        assigned_to: "{{ doc.deal_owner or '' }}",
        reference_doctype: 'CRM Deal',
        reference_docname: '{{ doc.name }}',
        due_date: '{{ frappe.utils.add_days(frappe.utils.nowdate(), 1) }}',
      },
    }),
    step_condition: '',
    parent_step: 0,
    branch: '',
  }
}
