export function undoEdit(editId, table, recordId) {
  fetch(`/${table}/${recordId}/undo/${editId}`, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  }).then(resp => {
    if (resp.ok) {
      location.reload();
    } else {
      alert('Undo failed');
    }
  });
}
window.undoEdit = undoEdit;
