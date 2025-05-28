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
  $('#layout-grid').css('grid-template-rows', `repeat(${extraRows}, 1em)`);
  console.log("Calculated grid rows",extraRows)
}

function onLoadJS(){
  initLayout();
  calculateGridRows();
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
      colSpan: widthUnits * PCT_SNAP,
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

function handleResizeMouseDown(e) {
  console.debug('Entering handleResizeMouseDown', e);
  const handle = e.target.closest('.ui-resizable-handle');
  if (!handle) return;
  const direction = Array.from(handle.classList)
    .find(c => c.startsWith('ui-resizable-') && c !== 'ui-resizable-handle');
  const field = handle.closest('.draggable-field').dataset.field;
  console.log(`Resize handle clicked: field=${field}, direction=${direction}`);
}
// Just logging
function handleMouseUp(e) {
  console.debug('Entering handleMouseUp', e);
}


function handleFieldMouseDown(e) {
  console.debug('Entering handleFieldMouseDown', e);
  // Skip clicks on resize handles
  if (e.target.closest('.ui-resizable-handle')) return;
  const fieldEl = e.target.closest('.draggable-field');
  if (!fieldEl) return;
  const field = fieldEl.dataset.field;
  console.log(`Field clicked for drag: ${field}`);
}

function handleSaveLayout() {
  // re-fetch our DOM elements so they exist in this scope
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const saveLayoutBtn       = document.getElementById('save-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const layoutGrid          = document.getElementById('layout-grid');

  // tear down the jQuery-UI behaviors
  $('.draggable-field').resizable('destroy').draggable('destroy');

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
  saveLayoutBtn.classList.remove('hidden');
  addFieldBtn.classList.add('hidden');
  toggleEditLayoutBtn.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', function() {
  // Initialize GRID_SIZE before layout actions
  onLoadJS();
  window.addEventListener('resize', () => {
    const layoutGrid = document.getElementById('layout-grid');
    CONTAINER_WIDTH = layoutGrid.clientWidth;

    // CRITICAL FIX: Explicitly refresh containment boundaries
    $('.draggable-field').draggable('option', 'containment', '#layout-grid');

    console.log("Updated container width and draggable containment:", CONTAINER_WIDTH);
  });

  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const saveLayoutBtn       = document.getElementById('save-layout');
  const layoutGrid          = document.getElementById('layout-grid');

  // Enter edit mode
  toggleEditLayoutBtn.addEventListener('click', function() {
    editModeButtons();

  $('.draggable-field')
    .resizable({
      handles: 'n, e, s, w, ne, se, sw, nw',
      start(e, ui) {
        const el = this;
        const f  = el.dataset.field;
        el._prevRect = { ...layoutCache[f] };
      },
      stop(e, ui) {
        const el = this;
        const f  = el.dataset.field;
        const prev = el._prevRect || layoutCache[f];

        // Only update size; keep original position
        const computedColSpan = Math.round(ui.size.width / CONTAINER_WIDTH * 100 / PCT_SNAP) * PCT_SNAP;
        const rowEm = parseFloat(getComputedStyle(document.documentElement).fontSize);
        const computedRowSpan = Math.round(ui.size.height / rowEm);

        layoutCache[f] = {
          colStart:  prev.colStart,
          colSpan:   computedColSpan,
          rowStart:  prev.rowStart,
          rowSpan:   computedRowSpan
        };

        // Clear px styles
        el.style.left = '';
        el.style.top = '';
        el.style.width = '';
        el.style.height = '';
        el.style.position = '';

        // Apply grid
        el.style.gridColumn = `${prev.colStart / PCT_SNAP + 1} / span ${computedColSpan / PCT_SNAP}`;
        el.style.gridRow    = `${prev.rowStart + 1} / span ${computedRowSpan}`;
      }
    })
  .draggable({
  containment: '#layout-grid',
  start: function(e, ui) {
    const el = ui.helper[0];
    const f  = el.dataset.field;
    el._prevRect = { ...layoutCache[f] };

    const gridRect = document.getElementById('layout-grid').getBoundingClientRect();
    const elRect = el.getBoundingClientRect();

    const offsetLeft = elRect.left - gridRect.left;
    const offsetTop  = elRect.top  - gridRect.top;

    el.style.left = `${offsetLeft}px`;
    el.style.top  = `${offsetTop}px`;
    el.style.position = 'absolute';

    void el.offsetHeight;

    console.log('▶️ Applied pixel offsets before drag:', offsetLeft, offsetTop);
  },
  stop: function(e, ui) {
    const el = ui.helper[0];
    console.log('Offset Parent:', ui.helper.offsetParent()[0]);
    console.log('Raw ui.position.left:', ui.position.left);
    console.log('Raw ui.position.top:', ui.position.top);
    console.log('CONTAINER_WIDTH:', CONTAINER_WIDTH);
    console.log('Container offset:', $('#layout-grid').offset());
    console.log('Dragged element offset:', $(el).offset());
    const f  = el.dataset.field;
    console.log('After Move layoutCache:', layoutCache);

    const computedColStart  = Math.round(ui.position.left  / CONTAINER_WIDTH * 100 / PCT_SNAP) * PCT_SNAP;
    const computedColSpan   = Math.round($(el).width()     / CONTAINER_WIDTH * 100 / PCT_SNAP) * PCT_SNAP;
    const rowEm             = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const computedRowStart  = Math.floor(ui.position.top    / rowEm);
    const computedRowSpan   = Math.round($(el).height()    / rowEm);

    const newRect = {
      colStart:  computedColStart,
      colSpan:   computedColSpan,
      rowStart:  computedRowStart,
      rowSpan:   computedRowSpan
    };

    console.log('Proposed newRect:', newRect);
    console.log('Existing layoutCache:', layoutCache);

    for (const [other, otherRect] of Object.entries(layoutCache)) {
      if (other === f) continue;
      console.log('Checking collision for:', newRect, 'against:', layoutCache);
      if (intersects(newRect, otherRect)) {
        console.warn(`⚠️ Collision dragging ${f} vs ${other}`);
        return revertPosition(el);
      }
    }

    layoutCache[f] = newRect;

    el.style.left     = '';
    el.style.top      = '';
    el.style.width    = '';
    el.style.height   = '';
    el.style.position = '';

    el.style.gridColumn = `${computedColStart / PCT_SNAP + 1} / span ${computedColSpan / PCT_SNAP}`;
    el.style.gridRow    = `${computedRowStart + 1} / span ${computedRowSpan}`;
  }
});
    console.log('Initial layoutCache:', layoutCache);  // Fires on entering edit mode; shows starting coordinates
  });
  saveLayoutBtn.addEventListener('click', handleSaveLayout);
  resetLayoutBtn.addEventListener('click', reset_layout);
  // Only run resize logic if the click landed on one of the resize handles
  layoutGrid.addEventListener('mousedown', e => {
  if (!e.target.closest('.ui-resizable-handle')) return;
  handleResizeMouseDown(e);
  });
  layoutGrid.addEventListener('mousedown', handleFieldMouseDown);
  layoutGrid.addEventListener('mouseup', handleMouseUp);

});

