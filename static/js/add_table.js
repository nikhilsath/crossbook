export function openAddTableModal() {
  document.getElementById('addTableModal').classList.remove('hidden');
}

export function closeAddTableModal() {
  document.getElementById('addTableModal').classList.add('hidden');
  const err = document.getElementById('tableError');
  if (err) err.textContent = '';
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
        document.getElementById('tableError').textContent = data.error;
      } else {
        window.location.reload();
      }
    })
    .catch(() => {
      document.getElementById('tableError').textContent = 'Failed to create table';
    });
}

window.openAddTableModal = openAddTableModal;
window.closeAddTableModal = closeAddTableModal;
window.submitNewTable = submitNewTable;
