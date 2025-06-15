import { submitFieldAjax } from './field_ajax.js';

// Helper to fetch the HTML for a specific field either in view or edit mode
async function fetchFieldHTML(field, edit) {
  const url = new URL(window.location.href);
  if (edit) {
    url.searchParams.set('edit', field);
  } else {
    url.searchParams.delete('edit');
  }
  const resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
  const text = await resp.text();
  const doc = new DOMParser().parseFromString(text, 'text/html');
  const el = doc.querySelector(`.draggable-field[data-field="${field}"]`);
  return el ? el.innerHTML : null;
}

// Minimal inline version of editor.js initialization for Quill
function initQuill(container) {
  if (typeof Quill === 'undefined') return;
  container.querySelectorAll('[data-quill]').forEach(el => {
    const form = el.closest('form');
    if (!form) return;
    let input = form.querySelector('input[name="new_value"]');
    if (!input) {
      input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'new_value';
      form.appendChild(input);
    }
    const quill = new Quill(el, { theme: 'snow' });
    input.value = quill.root.innerHTML;
    quill.on('text-change', () => {
      input.value = quill.root.innerHTML;
      if (form.hasAttribute('data-autosave')) {
        submitFieldAjax(form);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('layout-grid');
  if (!grid) return;

  let currentEl = null;

  grid.addEventListener('click', async (e) => {
    if (grid.classList.contains('editing')) return;
    const fieldEl = e.target.closest('.draggable-field');
    if (!fieldEl) return;
    if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON', 'A'].includes(e.target.tagName)) {
      return;
    }

    const field = fieldEl.dataset.field;
    const type = fieldEl.dataset.type;
    if (type === 'boolean' || fieldEl.querySelector('form') || currentEl) return;

    const html = await fetchFieldHTML(field, true);
    if (!html) return;
    fieldEl.innerHTML = html;
    fieldEl.classList.add('active-edit');
    initQuill(fieldEl);
    currentEl = fieldEl;

    const form = fieldEl.querySelector('form');
    const handleClickAway = async (evt) => {
      if (fieldEl.contains(evt.target)) return;
      document.removeEventListener('click', handleClickAway);
      try {
        if (form) await submitFieldAjax(form);
      } catch (err) {
        console.error('submitFieldAjax failed', err);
      } finally {
        const newHtml = await fetchFieldHTML(field, false);
        if (newHtml) {
          fieldEl.innerHTML = newHtml;
        }
        fieldEl.classList.remove('active-edit');
        currentEl = null;
      }
    };
    document.addEventListener('click', handleClickAway);
  });
});
