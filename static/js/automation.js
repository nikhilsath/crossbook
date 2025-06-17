async function fetchRules() {
  const resp = await fetch('/admin/api/automation/rules');
  const rules = await resp.json();
  const table = document.getElementById('rules-table');
  table.innerHTML = '<tr><th>ID</th><th>Name</th><th>Table</th><th>Runs</th><th>Actions</th></tr>' +
    rules.map(r => `<tr>
      <td>${r.id}</td>
      <td>${r.name}</td>
      <td>${r.table_name}</td>
      <td>${r.run_count || 0}</td>
      <td class="space-x-1">
        <button data-id="${r.id}" class="run btn-primary px-2 py-0.5 text-xs rounded">Run</button>
        <button data-id="${r.id}" class="reset btn-secondary px-2 py-0.5 text-xs rounded">Reset</button>
        <button data-id="${r.id}" class="edit btn-secondary px-2 py-0.5 text-xs rounded">Edit</button>
        <button data-id="${r.id}" class="delete btn-danger px-2 py-0.5 text-xs rounded">Delete</button>
        <button data-id="${r.id}" class="logs btn-secondary px-2 py-0.5 text-xs rounded">Logs</button>
      </td>
    </tr>`).join('');
}

function openRuleModal(rule) {
  document.getElementById('ruleModalTitle').textContent = rule ? 'Edit Rule' : 'New Rule';
  document.getElementById('rule-id').value = rule ? rule.id : '';
  document.getElementById('rule-name').value = rule ? rule.name : '';
  document.getElementById('rule-table').value = rule ? rule.table_name : '';
  document.getElementById('rule-cond-field').value = rule ? rule.condition_field : '';
  document.getElementById('rule-cond-op').value = rule ? rule.condition_operator : 'equals';
  document.getElementById('rule-cond-value').value = rule ? rule.condition_value : '';
  document.getElementById('rule-action-field').value = rule ? rule.action_field : '';
  document.getElementById('rule-action-value').value = rule ? rule.action_value : '';
  document.getElementById('rule-schedule').value = rule ? rule.schedule : 'none';
  document.getElementById('rule-run-on-import').checked = rule ? !!rule.run_on_import : false;
  document.getElementById('ruleModal').classList.remove('hidden');
  document.addEventListener('keydown', ruleEscHandler);
}

function closeRuleModal() {
  document.getElementById('ruleModal').classList.add('hidden');
  document.removeEventListener('keydown', ruleEscHandler);
}

function ruleEscHandler(e) {
  if (e.key === 'Escape') closeRuleModal();
}

async function submitRuleForm(e) {
  e.preventDefault();
  const id = document.getElementById('rule-id').value;
  const payload = {
    name: document.getElementById('rule-name').value,
    table_name: document.getElementById('rule-table').value,
    condition_field: document.getElementById('rule-cond-field').value,
    condition_operator: document.getElementById('rule-cond-op').value,
    condition_value: document.getElementById('rule-cond-value').value,
    action_field: document.getElementById('rule-action-field').value,
    action_value: document.getElementById('rule-action-value').value,
    run_on_import: document.getElementById('rule-run-on-import').checked,
    schedule: document.getElementById('rule-schedule').value,
  };
  if (id) {
    await fetch(`/admin/api/automation/rules/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } else {
    await fetch('/admin/api/automation/rules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }
  closeRuleModal();
  fetchRules();
}

async function deleteRule(id) {
  if (!confirm('Delete rule ' + id + '?')) return;
  await fetch(`/admin/api/automation/rules/${id}/delete`, { method: 'POST' });
  fetchRules();
}

async function runRule(id) {
  await fetch(`/admin/api/automation/rules/${id}/run`, { method: 'POST' });
  fetchRules();
}

async function resetRule(id) {
  await fetch(`/admin/api/automation/rules/${id}/reset`, { method: 'POST' });
  fetchRules();
}

let activeLogRuleId = null;

async function openLogsModal(id) {
  activeLogRuleId = id;
  const resp = await fetch(`/admin/api/automation/rules/${id}/logs`);
  const logs = await resp.json();
  const table = document.getElementById('logs-table');
  table.innerHTML = '<tr><th>ID</th><th>Table</th><th>Record</th><th>Field</th><th>Old</th><th>New</th><th>Time</th><th></th></tr>' +
    logs.map(l => `<tr>
      <td>${l.id}</td><td>${l.table_name}</td><td>${l.record_id}</td>
      <td>${l.field_name}</td><td>${l.old_value ?? ''}</td>
      <td>${l.new_value ?? ''}</td><td>${l.timestamp}</td>
      <td><button data-id="${l.id}" class="rollback btn-danger px-2 py-0.5 text-xs rounded">Rollback</button></td>
    </tr>`).join('');
  document.getElementById('logsModal').classList.remove('hidden');
  document.addEventListener('keydown', logsEscHandler);
}

function closeLogsModal() {
  document.getElementById('logsModal').classList.add('hidden');
  document.removeEventListener('keydown', logsEscHandler);
}

function logsEscHandler(e) {
  if (e.key === 'Escape') closeLogsModal();
}

async function rollbackEntry(id) {
  await fetch('/admin/api/automation/rollback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ entry_id: id }),
  });
  if (activeLogRuleId !== null) openLogsModal(activeLogRuleId);
  fetchRules();
}

// event delegation
document.addEventListener('click', e => {
  if (e.target.id === 'new-rule') {
    openRuleModal(null);
  } else if (e.target.classList.contains('edit')) {
    const id = e.target.getAttribute('data-id');
    fetch('/admin/api/automation/rules')
      .then(r => r.json())
      .then(list => {
        const rule = list.find(r => r.id == id);
        if (rule) openRuleModal(rule);
      });
  } else if (e.target.classList.contains('delete')) {
    deleteRule(e.target.getAttribute('data-id'));
  } else if (e.target.classList.contains('run')) {
    runRule(e.target.getAttribute('data-id'));
  } else if (e.target.classList.contains('reset')) {
    resetRule(e.target.getAttribute('data-id'));
  } else if (e.target.classList.contains('logs')) {
    openLogsModal(e.target.getAttribute('data-id'));
  } else if (e.target.classList.contains('rollback')) {
    rollbackEntry(e.target.getAttribute('data-id'));
  }
});

document.getElementById('rule-form').addEventListener('submit', submitRuleForm);

document.addEventListener('DOMContentLoaded', fetchRules);

window.closeRuleModal = closeRuleModal;
window.closeLogsModal = closeLogsModal;
