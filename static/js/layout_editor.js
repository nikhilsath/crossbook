// layout_editor.js

// Global state for layout editing
const GRID_SIZE = 20; // Size of each grid unit in pixels
const layoutCache = {};        // Tracks last valid positions
let editMode = false;

function setFieldsDisabled(disabled) {
  document
    .querySelectorAll('#layout-grid .draggable-field')
    .forEach(card => {
      // disable _all_ inputs, selects, textareas inside this card
      card.querySelectorAll('input, select, textarea')
          .forEach(ctrl => ctrl.disabled = disabled);
    });
}

document.addEventListener("DOMContentLoaded", () => {
  const editBtn    = document.getElementById('toggle-edit-layout');
  const resetBtn   = document.getElementById('reset-layout');
  const addFieldBtn= document.getElementById('add-field');
  const container  = document.getElementById('layout-grid');

  editBtn.addEventListener('click', () => {
    editMode = !editMode;
    container.classList.toggle("editing");
    resetBtn.classList.toggle("hidden");
    if (addFieldBtn) addFieldBtn.classList.toggle("hidden");

    if (editMode) {
      enableLayoutEditing();
      editBtn.textContent = 'Stop Editing';
      setFieldsDisabled(true);
    } else {
      disableLayoutEditing();
      captureAllLayout();
      editBtn.textContent = 'Edit Layout';
      setFieldsDisabled(false);
    }
  });

  resetBtn.addEventListener('click', () => {
    resetLayout();
  });
});

// Read element metrics and convert to grid units
function getGridData(el) {
  const rawX   = parseFloat(el.getAttribute('data-x')) || 0;
  const rawY   = parseFloat(el.getAttribute('data-y')) || 0;
  const width  = el.offsetWidth;
  const height = el.offsetHeight;

  const x = Math.round(rawX / GRID_SIZE);
  const y = Math.round(rawY / GRID_SIZE);
  const w = Math.round(width / GRID_SIZE);
  const h = Math.round(height / GRID_SIZE);

  return { field: el.dataset.field, x, y, w, h };
}

// Update layoutCache for a single element
function updateCache(el) {
  const data = getGridData(el);
  layoutCache[data.field] = { ...data };
  console.log(`🔁 updateCache: ${data.field}`, data);
}

// Send full layout to server
function captureAllLayout() {
  console.log("🔄 Attempt to POST layout", layoutCache);
  const layout = [];
  document.querySelectorAll('.draggable-field').forEach(el => {
    const data = getGridData(el);
    layout.push(data);
    updateCache(el);
  });
  const table = window.location.pathname.split('/')[1];

  fetch(`/${table}/layout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ layout })
  })
  .then(res => {
    if (!res.ok) throw new Error('Failed to save layout');
    console.log('✅ Layout saved');
  })
  .catch(err => console.error('❌ Layout save error:', err));
}

// Enable interact.js behaviors for drag & resize without overlap checks
function enableLayoutEditing() {
  console.log('🟢 Enabling layout editing');
  // Cache initial positions
  document.querySelectorAll('.draggable-field').forEach(el => updateCache(el));

  interact('.draggable-field')
    .draggable({
      modifiers: [
        interact.modifiers.snap({
          targets: [ interact.snappers.grid({ x: GRID_SIZE, y: GRID_SIZE }) ],
          range: Infinity,
          relativePoints: [ { x: 0, y: 0 } ]
        })
      ],
      inertia: true,
      listeners: {
        move(event) {
          const target = event.target;
          const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
          const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
          target.style.transform = `translate(${x}px, ${y}px)`;
          target.setAttribute('data-x', x);
          target.setAttribute('data-y', y);
        },
        end(event) {
          updateCache(event.target);
          setTimeout(captureAllLayout, 10);
        }
      }
    })
    .resizable({
      edges: { top: true, left: true, bottom: true, right: true },
      modifiers: [
        interact.modifiers.snapSize({ targets: [ interact.snappers.grid({ width: GRID_SIZE, height: GRID_SIZE }) ] })
      ],
      listeners: {
        move(event) {
          const target = event.target;
          let x = parseFloat(target.getAttribute('data-x')) || 0;
          let y = parseFloat(target.getAttribute('data-y')) || 0;
          target.style.width  = `${event.rect.width}px`;
          target.style.height = `${event.rect.height}px`;
          x += event.deltaRect.left;
          y += event.deltaRect.top;
          target.style.transform = `translate(${x}px, ${y}px)`;
          target.setAttribute('data-x', x);
          target.setAttribute('data-y', y);
        },
        end(event) {
          updateCache(event.target);
          setTimeout(captureAllLayout, 10);
        }
      }
    });
}

// Disable interact.js behaviors
function disableLayoutEditing() {
  console.log('🔴 Disabling layout editing');
  interact('.draggable-field').unset();
}

// Reset layout to one-field-per-row
function resetLayout() {
  console.log('🟡 Resetting layout to one-field-per-row');
  document.querySelectorAll('.draggable-field').forEach(el => {
    el.style.transform = '';
    el.style.width     = '';
    el.style.height    = '';
    el.style.gridColumn = 'span 12';
    el.style.gridRow    = 'auto';
    el.removeAttribute('data-x');
    el.removeAttribute('data-y');
  });
  console.log('✅ Layout reset complete');
}
