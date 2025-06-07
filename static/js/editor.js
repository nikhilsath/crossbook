export function initQuillEditor(field, statusId) {
  const container = document.getElementById(`editor_${field}`);
  const hidden = document.getElementById(`hidden_${field}`);
  const statusEl = statusId ? document.getElementById(statusId) : null;
  if (!container || !hidden || typeof Quill === 'undefined') return;

  const quill = new Quill(container, {
    theme: 'snow',
    modules: {
      toolbar: [
        ['bold', 'italic', 'underline'],
        ['link'],
        [{ color: [] }]
      ]
    }
  });

  // Set starting content
  quill.root.innerHTML = hidden.value || container.innerHTML;

  let saveTimer;
  quill.on('text-change', () => {
    hidden.value = quill.root.innerHTML;
    clearTimeout(saveTimer);
    if (statusEl) statusEl.textContent = 'Saving…';
    saveTimer = setTimeout(() => {
      const form = hidden.form;
      fetch(form.action, {
        method: form.method || 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: new FormData(form)
      })
        .then(resp => {
          if (!resp.ok) throw new Error('Network response was not ok');
          if (statusEl) {
            statusEl.textContent = 'Saved';
            setTimeout(() => (statusEl.textContent = ''), 2000);
          }
        })
        .catch(err => {
          console.error(err);
          if (statusEl) statusEl.textContent = 'Save failed';
        });
    }, 1000);
  });

  // Initialize hidden value
  hidden.value = quill.root.innerHTML;
  return quill;
}
