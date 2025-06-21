import { openModal, closeModal } from './modal_helper.js';

function initDatabaseControls() {
  const uploadForm = document.getElementById('db-upload-form');
  if (uploadForm) {
    const fileInput = uploadForm.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
          console.log('File chosen:', fileInput.files[0].name);
        } else {
          console.log('File input cleared');
        }
      });
    }
    uploadForm.addEventListener('submit', e => {
      e.preventDefault();
      const fd = new FormData(uploadForm);
      fetch('/admin/config/db', {
        method: 'POST',
        body: fd,
        headers: { 'Accept': 'application/json' }
      })
        .then(r => {
          if (!r.ok) {
            throw new Error('Server responded with status ' + r.status);
          }
          return r.json();
        })
        .then(data => {
          if (data.redirect) {
            window.location.href = data.redirect;
            return;
          }
          if (data.db_path) {
            const disp = document.getElementById('db-path-display');
            if (disp) {
              disp.textContent = data.db_path;
              disp.classList.remove('text-red-600', 'text-green-600');
              const color = data.status === 'valid' ? 'text-green-600' : 'text-red-600';
              disp.classList.add(color);
            }
            window.location.reload();
          } else if (data.error) {
            console.error('Failed to change database:', data.error);
          } else {
            console.error('Failed to change database: no db_path returned');
          }
        })
        .catch(err => {
          console.error('Failed to change database:', err);
        });
    });
  }

}

export function openCreateDbModal() {
  openModal('createDbModal');
}

export function closeCreateDbModal() {
  closeModal('createDbModal');
  const err = document.getElementById('create-db-error');
  if (err) {
    err.textContent = '';
    err.classList.add('hidden');
  }
}

export function submitCreateDb(event) {
  if (event) event.preventDefault();
  const nameInput = document.getElementById('create-db-name');
  const name = nameInput.value.trim();
  if (!name) return;
  const fd = new FormData();
  fd.append('create_name', name);
  fetch('/admin/config/db', { method: 'POST', body: fd, headers: { 'Accept': 'application/json' } })
    .then(r => r.json())
    .then(data => {
      if (data.redirect) {
        window.location.href = data.redirect;
        return;
      }
      if (data.db_path) {
        const disp = document.getElementById('db-path-display');
        if (disp) {
          disp.textContent = data.db_path;
          disp.classList.remove('text-red-600', 'text-green-600');
          const color = data.status === 'valid' ? 'text-green-600' : 'text-red-600';
          disp.classList.add(color);
        }
        window.location.reload();
      } else if (data.error) {
        const err = document.getElementById('create-db-error');
        if (err) {
          err.textContent = data.error;
          err.classList.remove('hidden');
        }
      }
    });
}

document.addEventListener('DOMContentLoaded', () => {
  initDatabaseControls();
});

window.openCreateDbModal = openCreateDbModal;
window.closeCreateDbModal = closeCreateDbModal;
window.submitCreateDb = submitCreateDb;
