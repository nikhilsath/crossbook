const PCT_SNAP = 5;                // snap to 5% steps
let CONTAINER_WIDTH;

const defaultFieldWidth = {};
const defaultFieldHeight = {};
if (window.FIELD_LAYOUT_DEFAULTS) {
  for (const [type, sizes] of Object.entries(window.FIELD_LAYOUT_DEFAULTS)) {
    const [w, h] = sizes;
    defaultFieldWidth[type] = w;
    defaultFieldHeight[type] = h;
  }
}

function initLayout() {
  const layoutGrid = document.getElementById('layout-grid');
  CONTAINER_WIDTH = layoutGrid.clientWidth;
}

function bindEventHandlers() {
  const saveLayoutBtn  = document.getElementById('save-layout');
  const resetLayoutBtn = document.getElementById('reset-layout');
  saveLayoutBtn.addEventListener('click', handleSaveLayout);
  resetLayoutBtn.addEventListener('click', resetLayout);
}

function onLoadJS(){
  initLayout();
  bindEventHandlers();
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
    // Intentionally silent if no previous rect
    return;
  }
  const startCol = prev.colStart;
  const spanCol  = prev.colSpan;
  const startRow = prev.rowStart;
  const spanRow  = prev.rowSpan;
  el.style.gridColumn = `${startCol} / span ${spanCol}`;
  el.style.gridRow    = `${startRow} / span ${spanRow}`;
  el.style.left     = '';
  el.style.width    = '';
  el.style.top      = '';
  el.style.height   = '';
  el.style.position = '';
  layoutCache[el.dataset.field] = { ...prev };
}

function resetLayout() {
  let curRow = 1;
  Object.entries(layoutCache).forEach(([field, rect]) => {
    const el = document.querySelector(`.draggable-field[data-field=\"${field}\"]`);
    if (!el || el.dataset.type === 'hidden') return;
    const widthUnits  = defaultFieldWidth[el.dataset.type]  || defaultFieldWidth.text;
    const heightUnits = defaultFieldHeight[el.dataset.type] || defaultFieldHeight.text;
    const colStart = 1;
    const rowStart = curRow;
    const rowSpan  = heightUnits;
    curRow += heightUnits;
    layoutCache[field] = { colStart, colSpan: widthUnits, rowStart, rowSpan };
    el.style.gridColumn = `${colStart} / span ${widthUnits}`;
    el.style.gridRow    = `${rowStart} / span ${rowSpan}`;
  });
  if (window.initAutosizeText) {
    window.initAutosizeText();
  }
}

function handleSaveLayout() {
  const layoutGrid          = document.getElementById('layout-grid');
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const saveLayoutBtn       = document.getElementById('save-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const headerToggleWrap    = document.getElementById('special-visibility-wrapper');
  toggleEditLayoutBtn.classList.remove('hidden');
  layoutGrid.classList.remove('editing');
  document.getElementById('field-style-menu')?.classList.add('hidden');
  addFieldBtn.classList.remove('hidden');
    document.querySelectorAll('.resize-handle')
.forEach(h => h.classList.add('hidden'));
  if (headerToggleWrap) headerToggleWrap.classList.add('hidden');
  const table = layoutGrid.dataset.table;
  const layoutEntries = Object.entries(layoutCache)
    .filter(([field]) => document.querySelector(`.draggable-field[data-field=\"${field}\"]`))
    .map(([field, rect]) => ({ field, colStart: rect.colStart, colSpan: rect.colSpan, rowStart: rect.rowStart, rowSpan: rect.rowSpan }));
  const payload = { layout: layoutEntries };
  fetch(`/${table}/layout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
    .then(response => {
      // ignore status logging in browser
      return response.json();
    })
    .then(data => {
      resetLayoutBtn.classList.add('hidden');
      saveLayoutBtn.classList.add('hidden');
      // layout save complete
      if (window.initAutosizeText) {
        window.initAutosizeText();
      }
    })
    .catch(() => {});
}

function editModeButtons() {
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const saveLayoutBtn       = document.getElementById('save-layout');
  const layoutGrid          = document.getElementById('layout-grid');
  const headerToggleWrap    = document.getElementById('special-visibility-wrapper');
  layoutGrid.classList.add('editing');
  resetLayoutBtn.classList.remove('hidden');
  addFieldBtn.classList.add('hidden');
  toggleEditLayoutBtn.classList.add('hidden');
  saveLayoutBtn.classList.remove('hidden');
  if (headerToggleWrap) headerToggleWrap.classList.remove('hidden');
}

function enableVanillaDrag() {
  const layoutGrid = document.getElementById('layout-grid');
  let isDragging = false;
  let startX, startY, startRect, field, fieldEl;

  layoutGrid.addEventListener('mousedown', e => {
    if (e.target.classList.contains('resize-handle')) return;
    fieldEl = e.target.closest('.draggable-field');
    field = fieldEl?.dataset.field;
    if (!fieldEl || !field) return;
    fieldEl._prevRect = { ...layoutCache[field] };
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
      colStart: newColStart + 1,
      colSpan:  startRect.colSpan,
      rowStart: newRowStart + 1,
      rowSpan:  startRect.rowSpan
    };

    // ▶️ Detect and highlight overlaps
    const hasOverlap = Object.entries(layoutCache).some(([otherKey, rect]) =>
      otherKey !== field && intersects(layoutCache[field], rect)
    );
    if (hasOverlap) {
      // snap back
      revertPosition(fieldEl);
      return;
    }

    // Clean up absolute positioning
    fieldEl.style.left = '';
    fieldEl.style.top = '';
    fieldEl.style.position = '';

    // Re-apply grid layout
    fieldEl.style.gridColumn = `${newColStart + 1} / span ${startRect.colSpan}`;
    fieldEl.style.gridRow    = `${newRowStart + 1} / span ${startRect.rowSpan}`;
    // Clearing up the following is required to allow resize again
    fieldEl.style.width  = '';
    fieldEl.style.height = '';

    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    if (window.initAutosizeText) {
      window.initAutosizeText();
    }
  }
}

function enableVanillaResize() {
  const layoutGrid = document.getElementById('layout-grid');
  const handles = document.querySelectorAll('.resize-handle');
  let isResizing = false;
  let handleType, fieldEl, field, startX, startY, startRect;
  if (layoutGrid.classList.contains('editing')) {
    handles.forEach(h => h.classList.remove('hidden'));
  } else {
    handles.forEach(h => h.classList.add('hidden'));
  }
  layoutGrid.addEventListener('mousedown', e => {
    if (!e.target.classList.contains('resize-handle')) return;
    e.preventDefault();
    // determine which corner was grabbed
    handleType = ['top-left','top-right','bottom-left','bottom-right']
                   .find(c => e.target.classList.contains(c));
    fieldEl = e.target.closest('.draggable-field');
    field   = fieldEl.dataset.field;
    startX  = e.clientX;
    startY  = e.clientY;
    startRect = { ...layoutCache[field] };
    fieldEl._prevRect = { ...startRect };
    isResizing = true;
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });

  function onMouseMove(e) {
    if (!isResizing) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const containerWidth = layoutGrid.clientWidth;
    const gridCols = 20;
    const gridCellWidth = containerWidth / gridCols;
    const deltaCols = Math.round(dx / gridCellWidth);
    const rowEm = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const deltaRows = Math.round(dy / rowEm);

    let { colStart, colSpan, rowStart, rowSpan } = startRect;
    let newColStart = colStart, newRowStart = rowStart;
    let newColSpan  = colSpan, newRowSpan  = rowSpan;

    if (handleType === 'bottom-right') {
      newColSpan = Math.max(1, colSpan + deltaCols);
      newRowSpan = Math.max(1, rowSpan + deltaRows);
    } else if (handleType === 'bottom-left') {
      newColStart = Math.max(1, colStart + deltaCols);
      newColSpan  = Math.max(1, colSpan - deltaCols);
      newRowSpan  = Math.max(1, rowSpan + deltaRows);
    } else if (handleType === 'top-right') {
      newRowStart = Math.max(1, rowStart + deltaRows);
      newRowSpan  = Math.max(1, rowSpan - deltaRows);
      newColSpan  = Math.max(1, colSpan + deltaCols);
    } else if (handleType === 'top-left') {
      newColStart = Math.max(1, colStart + deltaCols);
      newRowStart = Math.max(1, rowStart + deltaRows);
      newColSpan  = Math.max(1, colSpan - deltaCols);
      newRowSpan  = Math.max(1, rowSpan - deltaRows);
    }

    // apply live preview
    fieldEl.style.gridColumn = `${newColStart} / span ${newColSpan}`;
    fieldEl.style.gridRow    = `${newRowStart} / span ${newRowSpan}`;
    
  }

  function onMouseUp() {
    if (!isResizing) return;
    isResizing = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);

    // parse the new grid coords
    const partsCol = fieldEl.style.gridColumn.split(' ');
    const partsRow = fieldEl.style.gridRow.split(' ');
    const newRect = {
      colStart: parseInt(partsCol[0]),
      colSpan:  parseInt(partsCol[3]),
      rowStart: parseInt(partsRow[0]),
      rowSpan:  parseInt(partsRow[3]),
    };

    // collision check
    const hasOverlap = Object.entries(layoutCache).some(([key, rect]) =>
      key !== field && intersects(newRect, rect)
    );
    if (hasOverlap) {
      revertPosition(fieldEl);
    } else {
      layoutCache[field] = newRect;
    }
    if (window.initAutosizeText) {
      window.initAutosizeText();
    }
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
    enableVanillaDrag();
    enableVanillaResize();
  });
});
