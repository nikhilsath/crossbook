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
  textarea:  15,
  select: 4,
  text: 4,
  foreign_key: 3,
  boolean: 3,
  number: 3,
  multi_select: 5
};

function initLayout() {
  const layoutGrid = document.getElementById('layout-grid');
  CONTAINER_WIDTH = layoutGrid.clientWidth;
}

function intersects(a, b) {
  return (
    a.leftPct <  b.leftPct + b.widthPct  &&
    b.leftPct <  a.leftPct + a.widthPct  &&
    a.topEm   <  b.topEm   + b.heightEm &&
    b.topEm   <  a.topEm   + a.heightEm
  );
}
  
function revertPosition(el) {
  const prev = el._prevRect;
  if (!prev) {
    console.warn('No previous rect to revert for', el.dataset.field);
    return;
  }
  // 1️⃣ Restore horizontal (percent-based):
  el.style.left  = prev.leftPct  + '%';
  el.style.width = prev.widthPct + '%';
  // 2️⃣ Clear any old top/height px:
  el.style.top    = '';
  el.style.height = '';
  // 3️⃣ Restore vertical via CSS Grid row placement:
  //    (grid rows are 1-based)
  const rowStart = prev.topEm + 1;
  const rowSpan  = prev.heightEm;
  el.style.gridRowStart = rowStart;
  el.style.gridRowEnd   = `span ${rowSpan}`;
  // 4️⃣ Sync our in-memory cache back to prev:
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
      leftPct:  colStart,
      widthPct: widthUnits * PCT_SNAP,
      topEm:    rowStart,
      heightEm: rowSpan
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

function handleFieldMouseDown(e) {
  console.debug('Entering handleFieldMouseDown', e);
  // Skip clicks on resize handles
  if (e.target.closest('.ui-resizable-handle')) return;
  const fieldEl = e.target.closest('.draggable-field');
  if (!fieldEl) return;
  const field = fieldEl.dataset.field;
  console.log(`Field clicked for drag: ${field}`);
}

document.addEventListener('DOMContentLoaded', function() {
  // Initialize GRID_SIZE before layout actions
  initLayout();
  const extraRows = Object.keys(layoutCache).length * 10;
  $('#layout-grid').css('grid-template-rows', `repeat(${extraRows}, 1em)`);
  
  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const saveLayoutBtn       = document.getElementById('save-layout');
  const layoutGrid          = document.getElementById('layout-grid');

  // Enter edit mode
  toggleEditLayoutBtn.addEventListener('click', function() {
    layoutGrid.classList.add('editing');
    resetLayoutBtn.classList.remove('hidden');
    saveLayoutBtn.classList.remove('hidden');
    addFieldBtn.classList.add('hidden');
    toggleEditLayoutBtn.classList.add('hidden'); 

    $('.draggable-field')
  .resizable({
    containment: '#layout-grid',
    handles: 'n, e, s, w, ne, se, sw, nw',
    start(e, ui) {
      // Save old percent/em rect so we can revert if overlap
      const el = this;
      const f  = el.dataset.field;
      const prev = layoutCache[f];
      // store leftPct, widthPct, topEm, heightEm from the old cache
      el._prevRect = { ...prev };
      console.log('🛫 resizable start – prevRect:', prev);
    },
    stop(e, ui) {
      const el = this;
      const f  = el.dataset.field;
      console.log('[layout] drag stop raw px/size:', {
              left:   ui.position.left,
              top:    ui.position.top,
              width:  $(el).width(),
              height: $(el).height()
            });
      // 1) px → percent snapped
      const leftPct  = Math.round( ui.position.left  / CONTAINER_WIDTH * 100 / PCT_SNAP ) * PCT_SNAP;
      const widthPct = Math.round( ui.size.width      / CONTAINER_WIDTH * 100 / PCT_SNAP ) * PCT_SNAP;
      // 2) px → em snapped
      const rowEm    = parseFloat(getComputedStyle(document.documentElement).fontSize);
      const topEm    = Math.floor( ui.position.top    / rowEm );
      const heightEm = Math.round( ui.size.height     / rowEm );
      // 3) update cache
      layoutCache[f] = { leftPct, widthPct, topEm, heightEm };
      console.log('🔚 resizable stop – newRect:', layoutCache[f]);

      // 4) apply via CSS Grid
      //    clear px styles
      el.style.left   = '';
      el.style.top    = '';
      el.style.width  = '';
      el.style.height = '';
      el.style.position  = '';

      //    set gridColumn / gridRow
      //    NOTE: colStart = (leftPct / PCT_SNAP) + 1
      const colStart = leftPct / PCT_SNAP + 1;
      const colSpan  = widthPct / PCT_SNAP;
      const rowStart = topEm + 1;      // CSS grid is 1-based
      const rowSpan  = heightEm;
      el.style.gridColumn = `${colStart} / span ${colSpan}`;
      el.style.gridRow    = `${rowStart} / span ${rowSpan}`;
    }
  })
  .draggable({
  stop: function(e, ui) {
    const el = ui.helper[0];
    const f  = el.dataset.field;

    // Snap-to-grid calculations
    const leftPct  = Math.round(ui.position.left  / CONTAINER_WIDTH * 100 / PCT_SNAP) * PCT_SNAP;
    const widthPct = Math.round($(el).width()     / CONTAINER_WIDTH * 100 / PCT_SNAP) * PCT_SNAP;
    const rowEm    = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const topEm    = Math.floor(ui.position.top    / rowEm);
    const heightEm = Math.round($(el).height()    / rowEm);

    // Collision detection against existing fields
    const newRect = { leftPct, widthPct, topEm, heightEm };
    for (const [other, otherRect] of Object.entries(layoutCache)) {
      if (other === f) continue;
      if (intersects(newRect, otherRect)) {
        console.warn(`⚠️ Collision dragging ${f} vs ${other}`);
        return revertPosition(el);
      }
    }

    // No collision → commit
    layoutCache[f] = newRect;

    // Clear inline px styles
    el.style.left     = '';
    el.style.top      = '';
    el.style.width    = '';
    el.style.height   = '';
    el.style.position = '';

    // Reapply grid spans
    const colStart = leftPct / PCT_SNAP + 1;
    const colSpan  = widthPct / PCT_SNAP;
    const rowStart = topEm + 1;
    const rowSpan  = heightEm;
    el.style.gridColumn = `${colStart} / span ${colSpan}`;
    el.style.gridRow    = `${rowStart} / span ${rowSpan}`;
  }
});
    console.log('Initial layoutCache:', layoutCache);  // Fires on entering edit mode; shows starting coordinates
  });
  saveLayoutBtn.addEventListener('click', function() {
    // tear down the jQuery-UI behaviors
    $('.draggable-field').resizable('destroy').draggable('destroy');
    // flip the buttons back
    toggleEditLayoutBtn.classList.remove('hidden');
    layoutGrid.classList.remove('editing');
    // build the payload from our percent/em cache
    const table = layoutGrid.dataset.table;
    const layoutEntries = Object.entries(layoutCache)
      // only include fields still rendered (auto-filters out hidden ones too)
      .filter(([field]) => 
        document.querySelector(`.draggable-field[data-field="${field}"]`)
      )
      .map(([field, rect]) => ({
        field,
        leftPct:  rect.leftPct,
        widthPct: rect.widthPct,
        topEm:    rect.topEm,
        heightEm: rect.heightEm
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
      addFieldBtn.classList.remove('hidden');
    })
    .catch(err => console.error('Save layout failed:', err));
  });
  resetLayoutBtn.addEventListener('click', reset_layout);
  layoutGrid.addEventListener('mousedown', handleResizeMouseDown);
  layoutGrid.addEventListener('mousedown', handleFieldMouseDown);

});

