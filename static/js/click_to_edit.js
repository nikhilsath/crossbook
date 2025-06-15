import { submitFieldAjax } from './field_ajax.js';

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
    const type = fieldEl.dataset.type;

    console.log('[click_to_edit] clicked field:', field, 'type:', type);

    if (type === 'boolean') return;
    if (fieldEl.querySelector('form')) return;

    if (table && recordId && field) {
      const url = new URL(window.location.href);
      url.searchParams.set('edit', field);
      console.log('[click_to_edit] navigating to:', url.pathname + url.search);
      window.location.href = url.pathname + url.search;
    }
  });

  const url = new URL(window.location.href);
  const editField = url.searchParams.get('edit');
  if (editField) {
    const activeEl = document.querySelector(`.draggable-field[data-field="${editField}"]`);
    const form = activeEl ? activeEl.querySelector('form') : null;
    const handleClickAway = (e) => {
      if (activeEl && activeEl.contains(e.target)) return;
      document.removeEventListener('click', handleClickAway);
      Promise.resolve(form ? submitFieldAjax(form) : null).finally(() => {
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.delete('edit');
        window.location.href = newUrl.pathname + newUrl.search;
      });
    };
    document.addEventListener('click', handleClickAway);
  }
});
