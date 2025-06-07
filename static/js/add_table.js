export function openAddTableModal() {
  document.getElementById('addTableModal').classList.remove('hidden');
}

export function closeAddTableModal() {
  document.getElementById('addTableModal').classList.add('hidden');
  const err = document.getElementById('tableError');
  if (err) {
    err.textContent = '';
    err.classList.add('hidden');
  }
}

export function submitNewTable(event) {
  if (event) event.preventDefault();
  const name = document.getElementById('tableName').value.trim();
  const description = document.getElementById('tableDescription').value.trim();
  fetch('/add-table', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ table_name: name, description })
  })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        const err = document.getElementById('tableError');
        err.textContent = data.error;
        err.classList.remove('hidden');
      } else {
        window.location.reload();
      }
    })
    .catch(() => {
      const err = document.getElementById('tableError');
      err.textContent = 'Failed to create table';
      err.classList.remove('hidden');
    });
}

window.openAddTableModal = openAddTableModal;
window.closeAddTableModal = closeAddTableModal;
window.submitNewTable = submitNewTable;
