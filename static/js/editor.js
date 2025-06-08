import { submitFieldAjax } from './field_ajax.js';

// Intercept deprecated DOMNodeInserted listeners that Quill adds and replace
// them with a no-op MutationObserver. This avoids Chrome deprecation warnings.
(function() {
  const originalAdd = Element.prototype.addEventListener;
  Element.prototype.addEventListener = function(type, listener, options) {
    if (type === 'DOMNodeInserted') {
      new MutationObserver(() => {}).observe(this, { childList: true });
      return;
    }
    return originalAdd.call(this, type, listener, options);
  };
  // Helper to restore the native method after editors initialize
  window.restoreAddEventListener = () => {
    Element.prototype.addEventListener = originalAdd;
  };
})();

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

  // Restore default addEventListener after Quill initialization
  if (typeof window.restoreAddEventListener === 'function') {
    window.restoreAddEventListener();
  }
}

document.addEventListener('DOMContentLoaded', initEditors);
