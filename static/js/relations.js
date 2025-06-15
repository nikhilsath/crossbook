let modalData = {}; // Holds context for the modal interaction (source table, source id, and target table)
let relationTrigger = null;
let escHandler = (e) => {
  if (e.key === 'Escape') {
    closeModal();
  }
};

// Opens the relation modal and populates it with entries from the target table
export function openAddRelationModal(tableA, idA, tableB) {
  modalData = { tableA, idA, tableB }; // Save context for use during submit
  relationTrigger = document.activeElement;
  const modal = document.getElementById('relationModal');
  modal.classList.remove('hidden'); // Show modal
  document.addEventListener('keydown', escHandler);

  const select = document.getElementById('relationOptions');
  select.innerHTML = '<option>Loading...</option>'; // Temporary placeholder

  // Fetch JSON listing of records for the target table
  fetch(`/api/${tableB}/list`)
    .then(res => res.json())
    .then(options => {
      const targetTable = modalData.tableB;
      if (targetTable !== "content") {
        options.sort((a, b) => a.label.localeCompare(b.label));
      }

      select.innerHTML = "";
      options.forEach(({ id, label }) => {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = targetTable === "content" ? `#${id} – ${label}` : label;
        select.appendChild(opt);
      });
    });
}

// Closes the modal (used by the Cancel button)
export function closeModal() {
  document.getElementById('relationModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (relationTrigger) {
    relationTrigger.focus();
    relationTrigger = null;
  }
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

// Add support for closing dropdowns on outside click
document.addEventListener('click', (e) => {
  document.querySelectorAll('[data-multiselect-dropdown]').forEach(dropdown => {
    if (!dropdown.contains(e.target)) {
      dropdown.querySelector('[data-options]').classList.add('hidden');
    }
  });
});
