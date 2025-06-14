let measureCanvas;

export function fitText(el) {

  if (!measureCanvas) {
    measureCanvas = document.createElement('canvas');
  }
  const ctx = measureCanvas.getContext('2d');

  console.groupCollapsed('[autosize_text] fitText', el.dataset.field || el.textContent.trim());

  // Reset any previous inline size
  el.style.fontSize = '';

  const text = el.textContent.trim();
  if (!text) {
    console.warn('[autosize_text] empty text');
    console.groupEnd();
    return;
  }

  const style = window.getComputedStyle(el);
  const fontFamily = style.fontFamily || 'sans-serif';
  const fontWeight = style.fontWeight || 'normal';
  ctx.font = `${fontWeight} 10px ${fontFamily}`;
  const metrics = ctx.measureText(text);

  const width = el.clientWidth;
  const height = el.clientHeight;
  if (!width || !height) {
    console.warn('[autosize_text] zero size', width, height);
    console.groupEnd();
    return;
  }

  const sizeByWidth = (width * 0.9 / metrics.width) * 10;
  const sizeByHeight = height * 0.9; // because metrics were for 10px height
  let newSize = Math.floor(Math.min(sizeByWidth, sizeByHeight));
  if (newSize < 4) newSize = 4;
  console.debug('[autosize_text] metrics.width=', metrics.width, 'sizeByWidth=', sizeByWidth, 'sizeByHeight=', sizeByHeight, 'newSize=', newSize);
  el.style.fontSize = `${newSize}px`;
  console.debug('[autosize_text] applied fontSize', el.style.fontSize);
  console.groupEnd();
}

function makeEditable(displayEl) {
  if (displayEl._autosizeObserver) {
    displayEl._autosizeObserver.disconnect();
    delete displayEl._autosizeObserver;
  }
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
  const container = el.parentElement || el;
  const observer = new ResizeObserver(() => fitText(el));
  observer.observe(container);
  el._autosizeObserver = observer;
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
