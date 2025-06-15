// Context menu for styling fields on the detail view and dashboard widgets

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

function sendDashboardStyling(widgetId, styling) {
  fetch('/dashboard/style', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ widget_id: widgetId, styling })
  }).catch(err => console.error('Dashboard styling update failed', err));
}

document.addEventListener('DOMContentLoaded', () => {
  const layoutGrid = document.getElementById('layout-grid') ||
                     document.getElementById('dashboard-grid');
  if (!layoutGrid) return;
  const isDashboard = layoutGrid.id === 'dashboard-grid';

  const menu = document.createElement('div');
  menu.id = 'field-style-menu';
  window.fieldStyleMenu = menu;
  menu.className = 'absolute bg-white border rounded shadow p-2 space-y-1 hidden z-50 text-sm';
  menu.innerHTML = `
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="bold"> <span>Bold</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="italic"> <span>Italic</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="underline"> <span>Underline</span></label>
    <label class="flex items-center space-x-1">
      <span class="whitespace-nowrap mr-1">Size</span>
      <button type="button" data-size-act="dec" class="px-1 border rounded">-</button>
      <span data-opt="size-display" class="px-1 w-6 text-center"></span>
      <button type="button" data-size-act="inc" class="px-1 border rounded">+</button>
      <input type="hidden" data-opt="size" value="">
    </label>
    <div id="color-presets" class="flex space-x-1 mt-1"></div>
  `;
  document.body.appendChild(menu);

  let selectedColor = '#000000';
  const presetsDiv = menu.querySelector('#color-presets');
  const sizeInput = menu.querySelector('[data-opt="size"]');
  const sizeDisplay = menu.querySelector('[data-opt="size-display"]');
  const SIZE_MIN = 10;
  const SIZE_MAX = 48;
  const SIZE_STEP = 1;

  function updateSizeDisplay(val) {
    sizeDisplay.textContent = val || '';
  }

  menu.querySelector('[data-size-act="dec"]').addEventListener('click', () => {
    let val = parseInt(sizeInput.value, 10);
    if (isNaN(val)) val = 14;
    val = Math.max(SIZE_MIN, val - SIZE_STEP);
    sizeInput.value = val;
    updateSizeDisplay(val);
    menu.dispatchEvent(new Event('change'));
  });

  menu.querySelector('[data-size-act="inc"]').addEventListener('click', () => {
    let val = parseInt(sizeInput.value, 10);
    if (isNaN(val)) val = 14;
    val = Math.min(SIZE_MAX, val + SIZE_STEP);
    sizeInput.value = val;
    updateSizeDisplay(val);
    menu.dispatchEvent(new Event('change'));
  });
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
    if (fieldEl.dataset.type === 'textarea') return;
    e.preventDefault();
    currentEl = fieldEl;
    const styling = fieldEl._styling || {};
    menu.querySelector('[data-opt="bold"]').checked = !!styling.bold;
    menu.querySelector('[data-opt="italic"]').checked = !!styling.italic;
    menu.querySelector('[data-opt="underline"]').checked = !!styling.underline;
    sizeInput.value = styling.size || '';
    updateSizeDisplay(sizeInput.value);
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

    const styling = Object.assign({}, currentEl._styling, {
      bold: menu.querySelector('[data-opt="bold"]').checked,
      italic: menu.querySelector('[data-opt="italic"]').checked,
      underline: menu.querySelector('[data-opt="underline"]').checked,
      color: selectedColor,
      size: parseInt(sizeInput.value, 10) || null
    });
    currentEl._styling = styling;
    applyStyling(currentEl, styling);

    if (!isDashboard) {
      const table = layoutGrid.dataset.table;
      const field = currentEl.dataset.field;
      sendStyling(table, field, styling);
    } else {
      const widgetId = currentEl.dataset.widget;
      if (widgetId) {
        sendDashboardStyling(widgetId, styling);
      }
    }
  });
});

window.applyFieldStyling = applyStyling;
