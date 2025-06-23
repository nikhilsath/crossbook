const triggers = {};
const handlers = {};

export function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  triggers[id] = document.activeElement;
  modal.classList.remove('hidden');
  handlers[id] = (e) => {
    if (e.key === 'Escape') {
      closeModal(id);
    }
  };
  document.addEventListener('keydown', handlers[id]);
}

export function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add('hidden');
  if (handlers[id]) {
    document.removeEventListener('keydown', handlers[id]);
    delete handlers[id];
  }
  if (triggers[id]) {
    triggers[id].focus();
    delete triggers[id];
  }
}

// make modal functions globally accessible so templates can use them directly
window.openModal = openModal;
window.closeModal = closeModal;
