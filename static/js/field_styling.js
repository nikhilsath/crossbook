// Context menu for styling fields on the detail view

function applyStyling(el, styling) {
  el.classList.toggle('font-bold', !!styling.bold);
  el.classList.toggle('italic', !!styling.italic);
  el.classList.toggle('underline', !!styling.underline);
  el.style.color = styling.color || '';
  const label = el.querySelector('div.text-sm.font-bold.capitalize.mb-1');
  if (label) label.classList.toggle('hidden', !!styling.hideName);
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
  menu.className = 'absolute bg-white border rounded shadow p-2 space-y-1 hidden z-50 text-sm';
  menu.innerHTML = `
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="hideName"> <span>Hide Name</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="bold"> <span>Bold</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="italic"> <span>Italic</span></label>
    <label class="flex items-center space-x-2"><input type="checkbox" data-opt="underline"> <span>Underline</span></label>
    <input id="field-color-input" type="color" data-opt="color" class="w-full h-6 p-0 border rounded cursor-pointer">
    <div id="color-presets" class="flex space-x-1 mt-1"></div>
  `;
  document.body.appendChild(menu);

  const colorInput = menu.querySelector('#field-color-input');
  const presetsDiv = menu.querySelector('#color-presets');
  const presetColors = ['#000000', '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
  presetsDiv.innerHTML = presetColors.map(c =>
    `<button type="button" data-color="${c}" class="w-4 h-4 rounded border" style="background-color:${c}"></button>`
  ).join('');
  presetsDiv.addEventListener('click', e => {
    if (e.target.dataset.color) {
      colorInput.value = e.target.dataset.color;
      menu.dispatchEvent(new Event('change'));
    }
  });

  let currentEl;

  layoutGrid.addEventListener('contextmenu', e => {
    if (!layoutGrid.classList.contains('editing')) return;
    const fieldEl = e.target.closest('.draggable-field');
    if (!fieldEl) return;
    e.preventDefault();
    currentEl = fieldEl;
    const styling = fieldEl._styling || {};
    menu.querySelector('[data-opt="hideName"]').checked = !!styling.hideName;
    menu.querySelector('[data-opt="bold"]').checked = !!styling.bold;
    menu.querySelector('[data-opt="italic"]').checked = !!styling.italic;
    menu.querySelector('[data-opt="underline"]').checked = !!styling.underline;
    colorInput.value = styling.color || '#000000';
    menu.style.left = `${e.pageX}px`;
    menu.style.top = `${e.pageY}px`;
    menu.classList.remove('hidden');
  });

  document.addEventListener('click', e => {
    if (!menu.contains(e.target)) menu.classList.add('hidden');
  });

  menu.addEventListener('change', () => {
    if (!currentEl) return;
    const table = layoutGrid.dataset.table;
    const field = currentEl.dataset.field;
    const styling = {
      hideName: menu.querySelector('[data-opt="hideName"]').checked,
      bold: menu.querySelector('[data-opt="bold"]').checked,
      italic: menu.querySelector('[data-opt="italic"]').checked,
      underline: menu.querySelector('[data-opt="underline"]').checked,
      color: colorInput.value
    };
    currentEl._styling = styling;
    applyStyling(currentEl, styling);
    sendStyling(table, field, styling);
  });
});

window.applyFieldStyling = applyStyling;
