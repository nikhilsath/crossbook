// Simplified text editing behaviour. The previous implementation dynamically
// resized text to fit its container, but this added a lot of complexity and
// often produced inconsistent results.  The logic below simply enables inline
// editing without attempting to measure or resize the font.

function fitText() {
  // no-op: resizing has been removed
}

function makeEditable(displayEl) {
  const value = displayEl.dataset.rawValue || displayEl.textContent.trim();
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
    const newDiv = document.createElement('div');
    newDiv.className = 'autosize-text';
    newDiv.dataset.field = displayEl.dataset.field;
    newDiv.dataset.recordId = displayEl.dataset.recordId;
    newDiv.dataset.updateUrl = displayEl.dataset.updateUrl;
    newDiv.dataset.label = displayEl.dataset.label;
    newDiv.dataset.rawValue = input.value;
    newDiv.innerHTML = `<b>${displayEl.dataset.label}:</b> ${input.value}`;
    form.replaceWith(newDiv);
    attach(newDiv);
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
  fitText(el);
  el.addEventListener('click', () => makeEditable(el));
}

export function initAutosizeText() {
  document.querySelectorAll('.autosize-text').forEach(el => attach(el));
}

function startAutosize() {
  requestAnimationFrame(initAutosizeText);
}

if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', startAutosize);
} else {
  startAutosize();
}

window.initAutosizeText = initAutosizeText;
