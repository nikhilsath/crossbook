import { openModal, closeModal } from './modal_helper.js';

export function openNewRecordModal() {
  openModal('new_record_modal');
}

export function closeNewRecordModal() {
  closeModal('new_record_modal');
}

window.openNewRecordModal = openNewRecordModal;
window.closeNewRecordModal = closeNewRecordModal;
