// Inline editing for text fields

function makeEditable(displayEl) {
  const value = displayEl.textContent.trim();
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = displayEl.dataset.updateUrl;
  form.className = 'inline';

  const hidden = document.createElement('input');
  hidden.type = 'hidden';
  hidden.name = 'field';
  hidden.value = displayEl.dataset.field;

  const input = document.createElement('input');
  input.type = 'text';
  input.name = 'new_value';
  input.value = value;
  input.className = 'border px-1 py-0.5 text-sm rounded';

  const status = document.createElement('span');
  status.className = 'ajax-status text-xs text-gray-500 ml-1 hidden';

  form.append(hidden, input, status);
  displayEl.replaceWith(form);
  input.focus();

  const finish = () => {
    submitFieldAjax(form);
    const newEl = document.createElement(displayEl.tagName.toLowerCase());
    newEl.className = displayEl.className;
    newEl.dataset.field = displayEl.dataset.field;
    newEl.dataset.recordId = displayEl.dataset.recordId;
    newEl.dataset.updateUrl = displayEl.dataset.updateUrl;
    newEl.textContent = input.value;
    form.replaceWith(newEl);
    attach(newEl);
  };

  input.addEventListener('blur', finish, { once: true });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      input.blur();
    }
  });
}

export function attach(el) {
  el.addEventListener('click', () => makeEditable(el));
}

export function initAutosizeText() {
  document.querySelectorAll('.autosize-text').forEach(el => attach(el));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAutosizeText);
} else {
  initAutosizeText();
}

window.initAutosizeText = initAutosizeText;
