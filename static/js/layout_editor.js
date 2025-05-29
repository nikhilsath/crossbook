const PCT_SNAP = 5;                // snap to 5% steps
let CONTAINER_WIDTH;

const defaultFieldWidth = {
  textarea:  12,
  select: 5,
  text: 12,
  foreign_key: 5,
  boolean: 3,
  number: 4,
  multi_select: 6
};
const defaultFieldHeight = {
  textarea:  18,
  select: 4,
  text: 4,
  foreign_key: 10,
  boolean: 7,
  number: 3,
  multi_select: 8
};

function initLayout() {
  const layoutGrid = document.getElementById('layout-grid');
  CONTAINER_WIDTH = layoutGrid.clientWidth;
  console.log("Initialized container width:", CONTAINER_WIDTH);
}

function calculateGridRows() {
  const extraRows = Object.keys(layoutCache).length * 10;
  console.log("Calculated grid rows",extraRows)
}


function bindEventHandlers() {
  const saveLayoutBtn  = document.getElementById('save-layout');
  const resetLayoutBtn = document.getElementById('reset-layout');
  saveLayoutBtn.addEventListener('click', handleSaveLayout);
  resetLayoutBtn.addEventListener('click', reset_layout);
  console.log("bindEventHandlers loaded ")
}


function onLoadJS(){
  initLayout();
  calculateGridRows();
  bindEventHandlers();
  console.log("onLoadJS wrapper log")
}

function intersects(a, b) {
  return (
    a.colStart <  b.colStart + b.colSpan  &&
    b.colStart <  a.colStart + a.colSpan  &&
    a.rowStart   <  b.rowStart   + b.rowSpan &&
    b.rowStart   <  a.rowStart   + a.rowSpan
  );
}
  
function revertPosition(el) {
  const prev = el._prevRect;
  if (!prev) {
    console.warn('No previous rect to revert for', el.dataset.field);
    return;
  }
  // Calculate grid positions from percentage/em values
  const colStart = (prev.colStart / PCT_SNAP) + 1;
  const colSpan = prev.colSpan / PCT_SNAP;
  const rowStart = prev.rowStart + 1;
  const rowSpan = prev.rowSpan;

  // Apply restored grid coordinates
  el.style.gridColumn = `${colStart} / span ${colSpan}`;
  el.style.gridRow = `${rowStart} / span ${rowSpan}`;

  // Clear potentially conflicting inline styles
  el.style.left = '';
  el.style.width = '';
  el.style.top = '';
  el.style.height = '';
  el.style.position = '';

  // Sync cache
  layoutCache[el.dataset.field] = { ...prev };

  console.log(
    '▶️ revertPosition called for',
    el.dataset.field,
    'with _prevRect=',
    prev
  );
}

function reset_layout() {
  console.group('reset_layout');
  // Reset cursor in "row units"
  let curRow = 1;
  // For each field in cache
  Object.entries(layoutCache).forEach(([field, rect]) => {
    const el = document.querySelector(`.draggable-field[data-field="${field}"]`);
    if (!el) return;
    // Skip hidden fields
    if (el.dataset.type === 'hidden') return;

    // Determine default size in grid-units
    const widthUnits  = defaultFieldWidth[el.dataset.type]  || defaultFieldWidth.text;
    const heightUnits = defaultFieldHeight[el.dataset.type] || defaultFieldHeight.text;

    const colStart = 1;                // always start at left
    const rowStart = curRow;           // integer row index
    const rowSpan  = heightUnits;      // number of rows (1em each)
    // Advance the cursor
    curRow += heightUnits;
    // Update cache using percent/em for payload
    layoutCache[field] = {
      colStart:  colStart,
      colSpan: widthUnits ,
      rowStart:    rowStart,
      rowSpan: rowSpan
    };
    // Apply via CSS Grid using unit counts
    el.style.gridColumn = `${colStart} / span ${widthUnits}`;
    el.style.gridRow    = `${rowStart} / span ${rowSpan}`;

    console.log(
      `Field "${field}": col ${colStart}→span ${widthUnits}, ` +
      `row ${rowStart}→span ${rowSpan}em`,
      '→ cache:', layoutCache[field]
    );
  });
  console.groupEnd();
}


function handleSaveLayout() {
  // re-fetch our DOM elements so they exist in this scope
  const layoutGrid          = document.getElementById('layout-grid');
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout')
  const addFieldBtn          = document.getElementById('add-field');
  const saveLayoutBtn  = document.getElementById('save-layout');
  const resetLayoutBtn = document.getElementById('reset-layout');

  // tear down the jQuery-UI behaviors

  // flip the buttons/UI back
  toggleEditLayoutBtn.classList.remove('hidden');
  layoutGrid.classList.remove('editing');
  addFieldBtn.classList.remove('hidden');
  // build payload from our percent/em cache
  const table = layoutGrid.dataset.table;
  const layoutEntries = Object.entries(layoutCache)
    .filter(([field]) =>
      document.querySelector(`.draggable-field[data-field="${field}"]`)
    )
    .map(([field, rect]) => ({
      field,
      colStart:  rect.colStart,
      colSpan: rect.colSpan,
      rowStart:    rect.rowStart,
      rowSpan: rect.rowSpan
    }));
  const payload = { layout: layoutEntries };

  console.log('Payload being sent:', JSON.stringify(payload, null, 2));
  fetch(`/${table}/layout`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload)
  })
  .then(response => {
    console.log('Server response status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Save result:', data);
    // hide the “save/reset” buttons again
    resetLayoutBtn.classList.add('hidden');
    saveLayoutBtn.classList.add('hidden');
  })
  .catch(err => console.error('Save layout failed:', err));
}

function editModeButtons() {
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const saveLayoutBtn       = document.getElementById('save-layout'); 
  const layoutGrid          = document.getElementById('layout-grid');
  console.debug('editModeButtons: toggling edit-mode controls');
  layoutGrid.classList.add('editing');
  resetLayoutBtn.classList.remove('hidden');
  addFieldBtn.classList.add('hidden');
  toggleEditLayoutBtn.classList.add('hidden');
  saveLayoutBtn.classList.remove('hidden');
}

function enableVanillaDrag() {
  const layoutGrid = document.getElementById('layout-grid');
  let isDragging = false;
  let startX, startY, startRect, field, fieldEl;

  layoutGrid.addEventListener('mousedown', e => {
    fieldEl = e.target.closest('.draggable-field');
    field = fieldEl?.dataset.field;
    if (!fieldEl || !field) return;

    const rect = fieldEl.getBoundingClientRect();
    fieldEl.style.width  = `${rect.width}px`;
    fieldEl.style.height = `${rect.height}px`;
    const gridRect = layoutGrid.getBoundingClientRect();
    startX = e.clientX;
    startY = e.clientY;

    startRect = {
      left:   rect.left - gridRect.left,
      top:    rect.top  - gridRect.top,
      ...layoutCache[field]
    };

    // Temporarily lift from grid layout
    fieldEl.style.gridColumn = '';
    fieldEl.style.gridRow = '';
    fieldEl.style.position = 'absolute';
    fieldEl.style.left = `${startRect.left}px`;
    fieldEl.style.top  = `${startRect.top}px`;

    isDragging = true;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });

  function onMouseMove(e) {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    const newLeft = startRect.left + dx;
    const newTop  = startRect.top  + dy;

    fieldEl.style.left = `${newLeft}px`;
    fieldEl.style.top  = `${newTop}px`;
  }

  function onMouseUp(e) {
    if (!isDragging) return;
    isDragging = false;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const containerWidth = layoutGrid.clientWidth;
    const rowEm = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const gridCols = 20;
    const gridCellWidth = containerWidth / gridCols;
    const newColStart = Math.floor((startRect.left + dx) / gridCellWidth); // integer from 0 to 19
    const newRowStart = Math.round((startRect.top + dy) / rowEm);
    layoutCache[field] = {
      colStart: newColStart,
      colSpan:  startRect.colSpan,
      rowStart: newRowStart,
      rowSpan:  startRect.rowSpan
    };
    // Clean up absolute positioning
    fieldEl.style.left = '';
    fieldEl.style.top = '';
    fieldEl.style.position = '';

    // Re-apply grid layout
    fieldEl.style.gridColumn = `${newColStart + 1} / span ${startRect.colSpan}`;
    fieldEl.style.gridRow    = `${newRowStart + 1} / span ${startRect.rowSpan}`;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }
}
// Main Listener, triggers on page load
document.addEventListener('DOMContentLoaded', function() {
  // All onload functions 
  onLoadJS();
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const layoutGrid          = document.getElementById('layout-grid');
  // Enter edit mode
  toggleEditLayoutBtn.addEventListener('click', function() {
    editModeButtons();
    enableVanillaDrag()

  layoutGrid.addEventListener('mousedown', function(e) {
    const fieldEl = e.target.closest('.draggable-field');
    const field = fieldEl?.dataset.field;
    if (!fieldEl || !field) return;

    console.log('Activating draggable for field:', field);
  });

    console.log('Initial layoutCache:', layoutCache);  // Fires on entering edit mode; shows starting coordinates
  });

});
