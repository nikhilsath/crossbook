async function fetchRules() {
  const resp = await fetch('/admin/api/automation/rules');
  const rules = await resp.json();
  const table = document.getElementById('rules-table');
  table.innerHTML = '<tr><th>ID</th><th>Name</th><th>Table</th><th>Runs</th><th></th></tr>' +
    rules.map(r => `<tr><td>${r.id}</td><td>${r.name}</td><td>${r.table_name}</td><td>${r.run_count || 0}</td><td><button data-id="${r.id}" class="run">Run</button></td></tr>`).join('');
}

document.addEventListener('click', async e => {
  if (e.target.classList.contains('run')) {
    const id = e.target.getAttribute('data-id');
    await fetch(`/admin/api/automation/rules/${id}/run`, {method:'POST'});
    fetchRules();
  }
});

document.addEventListener('DOMContentLoaded', fetchRules);
