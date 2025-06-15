// Context menu for styling fields on the detail view

function applyStyling(el, styling) {
  el.classList.toggle('font-bold', !!styling.bold);
  el.classList.toggle('italic', !!styling.italic);
  el.classList.toggle('underline', !!styling.underline);
  el.style.color = styling.color || '';
  el.style.fontSize = styling.size ? `${styling.size}px` : '';
  const label = el.querySelector('div.text-sm.font-bold.capitalize.mb-1');
  if (label) label.classList.remove('hidden');
}

function sendStyling(table, field, styling) {
  fetch(`/${table}/style`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ field, styling })
  }).catch(err => console.error('Styling update failed', err));
}

document.addEventListener('DOMContentLoaded', () => {
  const layoutGrid = document.getElementById('layout-grid');
  if (!layoutGrid) return;

  const menu = document.createElement('div');
  menu.id = 'field-style-menu';
  window.fieldStyleMenu = menu;
  menu.className = 'absolute bg-white border rounded shadow p-2 space-y-1 hidden z-50 text-sm';
  menu.innerHTML = `
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="bold"> <span>Bold</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="italic"> <span>Italic</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="underline"> <span>Underline</span></label>
    <label class="flex items-center space-x-2">
      <span class="whitespace-nowrap">Size</span>
      <input type="number" data-opt="size" min="10" max="48" step="1" class="w-16 border rounded px-1 text-xs">
    </label>
    <div id="color-presets" class="flex space-x-1 mt-1"></div>
  `;
  document.body.appendChild(menu);

  let selectedColor = '#000000';
  const presetsDiv = menu.querySelector('#color-presets');
  const presetColors = ['#000000', '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
  presetsDiv.innerHTML = presetColors.map(c =>
    `<button type="button" data-color="${c}" class="w-4 h-4 rounded border" style="background-color:${c}"></button>`
  ).join('');
  presetsDiv.addEventListener('click', e => {
    if (e.target.dataset.color) {
      selectedColor = e.target.dataset.color;
      menu.dispatchEvent(new Event('change'));
    }
  });

  let currentEl;
  let keyListener;

  layoutGrid.addEventListener('contextmenu', e => {
    if (!layoutGrid.classList.contains('editing')) return;
    const fieldEl = e.target.closest('.draggable-field');
    if (!fieldEl) return;
    e.preventDefault();
    currentEl = fieldEl;
    const styling = fieldEl._styling || {};
    menu.querySelector('[data-opt="bold"]').checked = !!styling.bold;
    menu.querySelector('[data-opt="italic"]').checked = !!styling.italic;
    menu.querySelector('[data-opt="underline"]').checked = !!styling.underline;
    menu.querySelector('[data-opt="size"]').value = styling.size || '';
    selectedColor = styling.color || '#000000';
    menu.style.left = `${e.pageX}px`;
    menu.style.top = `${e.pageY}px`;
    menu.classList.remove('hidden');
    keyListener = evt => {
      if (evt.key === 'Escape') {
        menu.classList.add('hidden');
        document.removeEventListener('keydown', keyListener);
        keyListener = null;
      }
    };
    document.addEventListener('keydown', keyListener);
  });

  document.addEventListener('click', e => {
    if (!menu.contains(e.target)) {
      menu.classList.add('hidden');
      if (keyListener) {
        document.removeEventListener('keydown', keyListener);
        keyListener = null;
      }
    }
  });

  menu.addEventListener('change', () => {
    if (!currentEl) return;
    const table = layoutGrid.dataset.table;
    const field = currentEl.dataset.field;

    const styling = Object.assign({}, currentEl._styling, {
      bold: menu.querySelector('[data-opt="bold"]').checked,
      italic: menu.querySelector('[data-opt="italic"]').checked,
      underline: menu.querySelector('[data-opt="underline"]').checked,
      color: selectedColor,
      size: parseInt(menu.querySelector('[data-opt="size"]').value, 10) || null
    });
    currentEl._styling = styling;
    applyStyling(currentEl, styling);
    sendStyling(table, field, styling);
  });
});

window.applyFieldStyling = applyStyling;
