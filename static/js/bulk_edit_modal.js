export function openBulkEditModal() {
  document.getElementById('bulkEditModal').classList.remove('hidden');
}

export function closeBulkEditModal() {
  document.getElementById('bulkEditModal').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
  // Placeholder for future initialization
});

window.openBulkEditModal = openBulkEditModal;
window.closeBulkEditModal = closeBulkEditModal;
