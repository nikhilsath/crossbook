export function fitText(el) {
  // Skip resizing text while the layout grid is actively being edited
  if (document.querySelector('#layout-grid.editing')) {
    return;
  }

  // Reset any inline size so we can start from a clean slate
  el.style.fontSize = '';

  const style = window.getComputedStyle(el);
  let fontSize = parseFloat(style.fontSize) || 12;

  // Allow the text to grow while it fits within its own container
  el.style.fontSize = fontSize + 'px';
  while (el.scrollWidth <= el.clientWidth && el.scrollHeight <= el.clientHeight) {
    const nextSize = fontSize + 1;
    el.style.fontSize = nextSize + 'px';
    if (el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight) {
      el.style.fontSize = fontSize + 'px';
      break;
    }
    fontSize = nextSize;
    if (nextSize > 500) break; // safety guard
  }

  // If something still overflows, shrink to fit
  fontSize = parseFloat(el.style.fontSize);
  while ((el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight) && fontSize > 4) {
    fontSize -= 1;
    el.style.fontSize = fontSize + 'px';
  }
}

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
    const newDiv = document.createElement('div');
    newDiv.className = 'autosize-text';
    newDiv.dataset.field = displayEl.dataset.field;
    newDiv.dataset.recordId = displayEl.dataset.recordId;
    newDiv.dataset.updateUrl = displayEl.dataset.updateUrl;
    newDiv.textContent = input.value;
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

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAutosizeText);
} else {
  initAutosizeText();
}

window.initAutosizeText = initAutosizeText;
