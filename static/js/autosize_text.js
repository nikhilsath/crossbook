let measureCanvas;

export function fitText(el) {
  // Skip resizing when layout grid is currently being edited
  if (document.querySelector('#layout-grid.editing')) {
    return;
  }

  if (!measureCanvas) {
    measureCanvas = document.createElement('canvas');
  }
  const ctx = measureCanvas.getContext('2d');

  // Reset any previous inline size
  el.style.fontSize = '';

  const text = el.textContent.trim();
  if (!text) return;

  const style = window.getComputedStyle(el);
  const fontFamily = style.fontFamily || 'sans-serif';
  const fontWeight = style.fontWeight || 'normal';
  ctx.font = `${fontWeight} 10px ${fontFamily}`;
  const metrics = ctx.measureText(text);

  const width = el.clientWidth;
  const height = el.clientHeight;
  if (!width || !height) return;

  const sizeByWidth = (width * 0.9 / metrics.width) * 10;
  const sizeByHeight = height * 0.9; // because metrics were for 10px height
  let newSize = Math.floor(Math.min(sizeByWidth, sizeByHeight));
  if (newSize < 4) newSize = 4;
  el.style.fontSize = `${newSize}px`;
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
