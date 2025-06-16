export function toggleAddRelation(tableA, idA, tableB) {
  const container = document.getElementById(`add-rel-${tableB}`);
  if (!container) return;
  container.classList.toggle('hidden');
  const select = container.querySelector('select');
  if (!container.dataset.loaded) {
    fetch(`/api/${tableB}/list`)
      .then(r => r.json())
      .then(options => {
        if (tableB !== 'content') {
          options.sort((a, b) => a.label.localeCompare(b.label));
        }
        select.innerHTML = '';
        options.forEach(opt => {
          const o = document.createElement('option');
          o.value = opt.id;
          o.textContent = tableB === 'content' ? `#${opt.id} – ${opt.label}` : opt.label;
          select.appendChild(o);
        });
        container.dataset.loaded = '1';
      });
  }
  select.dataset.tableA = tableA;
  select.dataset.idA = idA;
}

export function submitRelation(tableB) {
  const select = document.getElementById(`rel-options-${tableB}`);
  if (!select) return;
  const tableA = select.dataset.tableA;
  const idA = parseInt(select.dataset.idA, 10);
  const idB = parseInt(select.value, 10);
  fetch('/relationship', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_a: tableA,
      id_a: idA,
      table_b: tableB,
      id_b: idB,
      action: 'add'
    })
  }).then(() => location.reload());
}

export function removeRelation(tableA, idA, tableB, idB) {
  fetch('/relationship', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_a: tableA,
      id_a: idA,
      table_b: tableB,
      id_b: idB,
      action: 'remove'
    })
  }).then(() => location.reload());
}

window.toggleAddRelation = toggleAddRelation;
window.submitRelation = submitRelation;
window.removeRelation = removeRelation;
