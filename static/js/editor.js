import { submitFieldAjax } from './field_ajax.js';

function initEditors() {
  document.querySelectorAll('[data-quill]').forEach(el => {
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
      if (form.hasAttribute('data-autosave') && typeof submitFieldAjax === 'function') {
        submitFieldAjax(form);
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', initEditors);
