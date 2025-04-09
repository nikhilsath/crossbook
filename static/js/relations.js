let modalData = {};

export function openAddRelationModal(tableA, idA, tableB) {
  modalData = { tableA, idA, tableB };
  const modal = document.getElementById('relationModal');
  modal.classList.remove('hidden');

  const select = document.getElementById('relationOptions');
  select.innerHTML = '<option>Loading...</option>';

  fetch(`/${tableB}`)
    .then(res => res.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const rows = Array.from(doc.querySelectorAll('tbody tr'));
      const options = [];

      rows.forEach(row => {
        const cols = row.querySelectorAll('td');
        if (cols.length >= 2) {
          const id = cols[0].innerText.trim();
          const label = cols[1].innerText.trim();
          options.push({ id, label });
        }
      });

      const targetTable = modalData.tableB;
      if (targetTable !== "content") {
        options.sort((a, b) => a.label.localeCompare(b.label));
      }

      select.innerHTML = "";

      options.forEach(({ id, label }) => {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = (targetTable === "content")
          ? `#${id} – ${label}`
          : label;
        select.appendChild(option);
      });
    });
}

export function closeModal() {
  document.getElementById('relationModal').classList.add('hidden');
}

export function submitRelation() {
  const idB = document.getElementById('relationOptions').value;
  fetch('/relationship', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_a: modalData.tableA,
      id_a: modalData.idA,
      table_b: modalData.tableB,
      id_b: parseInt(idB),
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
