import { openModal, closeModal } from './modal_helper.js';

function initDatabaseControls() {
  const uploadForm = document.getElementById('db-upload-form');
  if (uploadForm) {
    const fileInput = uploadForm.querySelector('input[type="file"]');
    const changeBtn = document.getElementById('change-db-btn');
    const uploadErr = document.getElementById('change-db-error');
    if (changeBtn) {
      changeBtn.disabled = true;
      changeBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }
    if (fileInput) {
      fileInput.addEventListener('change', () => {
        if (uploadErr) {
          uploadErr.textContent = '';
          uploadErr.classList.add('hidden');
        }
        if (fileInput.files && fileInput.files.length > 0) {
          console.log('File chosen:', fileInput.files[0].name);
          if (changeBtn) {
            changeBtn.disabled = false;
            changeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
          }
        } else {
          console.log('File input cleared');
          if (changeBtn) {
            changeBtn.disabled = true;
            changeBtn.classList.add('opacity-50', 'cursor-not-allowed');
          }
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
        .then(r => r.json().then(data => {
          if (!r.ok) throw data;
          return data;
        }))
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
            window.location.href = '/';
          } else if (data.error) {
            if (uploadErr) {
              uploadErr.textContent = data.error;
              uploadErr.classList.remove('hidden');
            } else {
              console.error('Failed to change database:', data.error);
            }
          } else {
            if (uploadErr) {
              uploadErr.textContent = 'Failed to change database';
              uploadErr.classList.remove('hidden');
            } else {
              console.error('Failed to change database: no db_path returned');
            }
          }
        })
        .catch(err => {
          if (uploadErr) {
            uploadErr.textContent = err.error || err.message;
            uploadErr.classList.remove('hidden');
          } else {
            console.error('Failed to change database:', err.error || err);
          }
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
    .then(r => r.json().then(data => {
      if (!r.ok) throw data;
      return data;
    }))
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
    })
    .catch(err => {
      const errEl = document.getElementById('create-db-error');
      if (errEl) {
        errEl.textContent = err.error || err.message;
        errEl.classList.remove('hidden');
      } else {
        console.error('Failed to create database:', err.error || err);
      }
    });
}

document.addEventListener('DOMContentLoaded', () => {
  initDatabaseControls();
});

window.openCreateDbModal = openCreateDbModal;
window.closeCreateDbModal = closeCreateDbModal;
window.submitCreateDb = submitCreateDb;
