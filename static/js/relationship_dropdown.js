export function toggleAddRelation(tableA, idA, tableB) {
  const container = document.getElementById(`add-rel-${tableB}`);
  if (!container) return;
  container.classList.toggle('hidden');
  const select = container.querySelector('select');
  const search = container.querySelector('input');
  select.dataset.tableA = tableA;
  select.dataset.idA = idA;
  if (!container.dataset.loaded) {
    fetchRelationOptions(tableB, '', select);
    container.dataset.loaded = '1';
  }
  search.focus();
}

function fetchRelationOptions(table, term, select) {
  fetch(`/api/${table}/list?search=${encodeURIComponent(term)}&limit=20`)
    .then(r => r.json())
    .then(options => {
      if (table !== 'content') {
        options.sort((a, b) => a.label.localeCompare(b.label));
      }
      select.innerHTML = '';
      options.forEach(opt => {
        const o = document.createElement('option');
        o.value = opt.id;
        o.textContent = table === 'content' ? `#${opt.id} – ${opt.label}` : opt.label;
        select.appendChild(o);
      });
    });
}

export function searchRelation(tableB, input) {
  const select = document.getElementById(`rel-options-${tableB}`);
  if (!select) return;
  fetchRelationOptions(tableB, input.value, select);
}

export function submitRelation(tableB) {
  const select = document.getElementById(`rel-options-${tableB}`);
  if (!select) return;
  const tableA = select.dataset.tableA;
  const idA = parseInt(select.dataset.idA, 10);
  const idB = parseInt(select.value, 10);
  const dir = document.querySelector(`input[name="rel-dir-${tableB}"]:checked`);
  const twoWay = dir ? dir.value === 'two' : true;
  fetch('/relationship', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_a: tableA,
      id_a: idA,
      table_b: tableB,
      id_b: idB,
      action: 'add',
      two_way: twoWay
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
window.searchRelation = searchRelation;
