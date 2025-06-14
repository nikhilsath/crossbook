document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('layout-grid');
  if (!grid) return;
  const table = grid.dataset.table;
  const recordId = grid.dataset.recordId;

  grid.addEventListener('click', (e) => {
    if (grid.classList.contains('editing')) return;
    const fieldEl = e.target.closest('.draggable-field');
    if (!fieldEl) return;
    if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(e.target.tagName)) {
      return;
    }
    const field = fieldEl.dataset.field;
    const fieldType = fieldEl.dataset.type;

    // Skip booleans so users can toggle them directly
    if (fieldType === 'boolean') return;

    if (fieldType === 'text') {
      const textEl = fieldEl.querySelector('.autosize-text');
      if (textEl) textEl.dispatchEvent(new Event('click'));
      return;
    }

    if (fieldEl.querySelector('form')) return;

    if (table && recordId && field) {
      window.location.href = `/${table}/${recordId}?edit=${field}`;
    }
  });
});

