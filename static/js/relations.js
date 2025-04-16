let modalData = {}; // Holds context for the modal interaction (source table, source id, and target table)

// Opens the relation modal and populates it with entries from the target table
export function openAddRelationModal(tableA, idA, tableB) {
  modalData = { tableA, idA, tableB }; // Save context for use during submit
  const modal = document.getElementById('relationModal');
  modal.classList.remove('hidden'); // Show modal

  const select = document.getElementById('relationOptions');
  select.innerHTML = '<option>Loading...</option>'; // Temporary placeholder

  // Fetch HTML for the list view of the target table (e.g. /character)
  fetch(`/${tableB}`)
    .then(res => res.text())
    .then(html => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      const rows = Array.from(doc.querySelectorAll('tbody tr'));
      const options = [];

      // Extract ID and label from each row (first 2 columns assumed to be ID and name/title)
      rows.forEach(row => {
        const cols = row.querySelectorAll('td');
        if (cols.length >= 2) {
          const id = cols[0].innerText.trim();
          const label = cols[1].innerText.trim();
          options.push({ id, label });
        }
      });

      const targetTable = modalData.tableB;
      // Sort alphabetically by label unless it's content (content sorted by ID instead)
      if (targetTable !== "content") {
        options.sort((a, b) => a.label.localeCompare(b.label));
      }

      // Populate dropdown with options
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

// Closes the modal (used by the Cancel button)
export function closeModal() {
  document.getElementById('relationModal').classList.add('hidden');
}

// Called when user clicks Add inside the modal to submit the selected relation
export function submitRelation() {
  const idB = document.getElementById('relationOptions').value;
  fetch('/relationship', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_a: modalData.tableA,
      id_a: modalData.idA,
      table_b: modalData.tableB,
      id_b: parseInt(idB), // Convert string to number
      action: 'add'
    })
  }).then(() => location.reload()); // Refresh to reflect changes
}

// Removes a relationship (called by ✖ button in detail view)
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
  }).then(() => location.reload()); // Refresh to reflect removal
}

// Autosave handler for multi_select checkboxes
export function submitMultiSelectAuto(formEl) {
  const formData = new FormData(formEl);
  fetch(formEl.action, {
    method: 'POST',
    body: formData
  }).then(() => location.reload());
}

// Add support for closing dropdowns on outside click
document.addEventListener('click', (e) => {
  document.querySelectorAll('[data-multiselect-dropdown]').forEach(dropdown => {
    if (!dropdown.contains(e.target)) {
      dropdown.querySelector('[data-options]').classList.add('hidden');
    }
  });
});

window.submitMultiSelectAuto = submitMultiSelectAuto;
