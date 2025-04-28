export function initRichTextEditor(field, statusId) {
  const editor = document.getElementById(`editor_${field}`);
  const hidden = document.getElementById(`hidden_${field}`);
  const statusEl = statusId ? document.getElementById(statusId) : null;

  // Clear any existing status
  if (statusEl) statusEl.textContent = '';

  if (!editor || !hidden) return;

  // Formatting buttons (bold, italic, underline)
  const container = editor.closest('.mb-4');
  const buttons = container.querySelectorAll('[data-command]');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-command');
      document.execCommand(cmd, false, null);
      editor.focus();
    });
  });

  // Debounced auto-save (1s after typing stops)
  let saveTimer;
  editor.addEventListener('input', () => {
    hidden.value = editor.innerHTML;
    clearTimeout(saveTimer);

    // Show "Saving..."
    if (statusEl) statusEl.textContent = 'Saving…';

    saveTimer = setTimeout(() => {
      const form = hidden.form;
      fetch(form.action, {
        method: form.method || 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: new FormData(form)
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        if (statusEl) {
          statusEl.textContent = 'Saved';
          setTimeout(() => { statusEl.textContent = ''; }, 2000);
        }
      })
      .catch(error => {
        console.error(error);
        if (statusEl) statusEl.textContent = 'Save failed';
      });
    }, 1000);
  });

  // Initialize hidden field
  hidden.value = editor.innerHTML;
}
