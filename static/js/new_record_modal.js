let recordTrigger = null;
const escHandler = (e) => {
  if (e.key === 'Escape') {
    closeNewRecordModal();
  }
};

export function openNewRecordModal() {
  recordTrigger = document.activeElement;
  document.getElementById('newRecordModal').classList.remove('hidden');
  document.addEventListener('keydown', escHandler);
}

export function closeNewRecordModal() {
  document.getElementById('newRecordModal').classList.add('hidden');
  document.removeEventListener('keydown', escHandler);
  if (recordTrigger) {
    recordTrigger.focus();
    recordTrigger = null;
  }
}

window.openNewRecordModal = openNewRecordModal;
window.closeNewRecordModal = closeNewRecordModal;
