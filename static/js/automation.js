async function loadRules() {
  const resp = await fetch('/admin/automation/rules');
  const rules = await resp.json();
  const tbody = document.querySelector('#automation-table tbody');
  tbody.innerHTML = '';
  rules.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.name}</td><td>${r.table_name}</td>` +
      `<td>${r.condition_field} ${r.condition_operator} ${r.condition_value}</td>` +
      `<td>${r.action_field} = ${r.action_value}</td>` +
      `<td>${r.schedule}</td><td>${r.run_count}</td>` +
      `<td><button data-run="${r.id}">Run</button> <button data-reset="${r.id}">Reset</button> <button data-logs="${r.id}">Logs</button></td>`;
    tbody.appendChild(tr);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadRules();
  document.body.addEventListener('click', async evt => {
    if (evt.target.dataset.run) {
      await fetch(`/admin/automation/trigger/${evt.target.dataset.run}`, {method:'POST'});
      loadRules();
    } else if (evt.target.dataset.reset) {
      await fetch(`/admin/automation/reset/${evt.target.dataset.reset}`, {method:'POST'});
      loadRules();
    } else if (evt.target.dataset.logs) {
      const resp = await fetch(`/admin/automation/logs/${evt.target.dataset.logs}`);
      const logs = await resp.json();
      alert(JSON.stringify(logs));
    }
  });
  const modal = document.getElementById('rule-modal');
  const form = document.getElementById('rule-form');
  document.getElementById('new-rule-btn').addEventListener('click', () => {
    form.reset();
    modal.classList.remove('hidden');
  });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form).entries());
    data.run_on_import = form.querySelector('input[name="run_on_import"]').checked ? 1 : 0;
    const id = data.id;
    delete data.id;
    const url = id ? `/admin/automation/rule/${id}` : '/admin/automation/rule';
    await fetch(url, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)});
    modal.classList.add('hidden');
    loadRules();
  });
});
