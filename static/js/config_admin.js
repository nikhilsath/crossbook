// Handle form submission for JSON config items

function initLayoutDefaultsForms() {
  document.querySelectorAll('form[data-json-key="layout_defaults"]').forEach(form => {
    form.addEventListener('submit', e => {
      const width = {};
      form.querySelectorAll('input[name^="width."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        width[key] = parseFloat(inp.value) || 0;
      });
      const height = {};
      form.querySelectorAll('input[name^="height."]').forEach(inp => {
        const key = inp.name.split('.')[1];
        height[key] = parseFloat(inp.value) || 0;
      });
      const hidden = form.querySelector('input[name="value"]');
      if (hidden) {
        hidden.value = JSON.stringify({ width, height });
      }
    });
  });
}

function initDatabaseControls() {
  const uploadForm = document.getElementById('db-upload-form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', e => {
      e.preventDefault();
      const fd = new FormData(uploadForm);
      fetch('/admin/config/db', {
        method: 'POST',
        body: fd
      }).then(() => window.location.reload());
    });
  }

  const createBtn = document.getElementById('create-db-btn');
  if (createBtn) {
    createBtn.addEventListener('click', () => {
      const name = prompt('Filename for new database (.db):');
      if (!name) return;
      const fd = new FormData();
      fd.append('create_name', name);
      fetch('/admin/config/db', { method: 'POST', body: fd })
        .then(() => window.location.reload());
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initLayoutDefaultsForms();
  initDatabaseControls();
});

