export function undoEdit(editId, table, recordId) {
  fetch(`/${table}/${recordId}/undo/${editId}`, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' }
  }).then(resp => {
    if (resp.ok) {
      if (typeof pendo !== 'undefined') {
        pendo.track('record_edit_undone', {
          table_name: table,
          record_id: String(recordId),
          edit_id: String(editId)
        });
      }
      location.reload();
    } else {
      alert('Undo failed');
    }
  });
}
window.undoEdit = undoEdit;
