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

  const createBtn = document.getElementById('create-db-btn');
  if (createBtn) {
    createBtn.addEventListener('click', () => {
      const name = prompt('Filename for new database (.db):');
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
          }
        });
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initDatabaseControls();
});
