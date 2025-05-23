const GRID_COLS = 12;
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
  textarea:  5,
  select: 2,
  text: 2,
  foreign_key: 3,
  boolean: 1,
  number: 1,
  multi_select: 3
};
let GRID_SIZE;

function initLayout() {
  const layoutGrid = document.getElementById('layout-grid');
  const gap = parseInt(getComputedStyle(layoutGrid).columnGap) || 0;
    // Calculate one column’s pixel width
    GRID_SIZE = Math.floor(
      (layoutGrid.clientWidth - gap * (GRID_COLS - 1)) / GRID_COLS
    );
  }

function intersects(a, b) {
  return a.x1 < b.x2 && b.x1 < a.x2
      && a.y1 < b.y2 && b.y1 < a.y2;
}

function reset_layout() {
  // Ensure GRID_SIZE is initialized
  if (typeof GRID_SIZE !== 'number') {
    initLayout();
  }
  console.group('reset_layout');
  let curYUnits = 0; // current vertical offset in grid-units

  // Debug: log all field keys in layoutCache before processing
  console.log('Fields in cache:', Object.keys(layoutCache));

  Object.keys(layoutCache).forEach(field => {
    // Skip fields without a rendered element
    const el = document.querySelector(`.draggable-field[data-field="${field}"]`);
    if (!el) return;

    // Skip hidden fields explicitly
    const type = el.dataset.type;
    if (type === 'hidden') return;

    // Determine default size in grid-units
    const widthUnits = defaultFieldWidth[type]  || defaultFieldWidth.text;
    const heightUnits = defaultFieldHeight[type] || defaultFieldHeight.text;
    // Calculate pixel positions
    const x1 = 0;
    // Debug: log GRID_SIZE to ensure it's defined
    console.log('GRID_SIZE:', GRID_SIZE);
    // Debug: log widthUnits and GRID_SIZE for x2 calculation
    console.log('widthUnits:', widthUnits, 'GRID_SIZE:', GRID_SIZE);
    const y1 = curYUnits * GRID_SIZE;
    const x2 = x1 + widthUnits * GRID_SIZE;
    const y2 = y1 + heightUnits * GRID_SIZE;

    // Log placement details
    console.log(`Field "${field}" [${type}]:`, { widthUnits, heightUnits, x1, y1, x2, y2 });

    // Advance vertical cursor
    curYUnits += heightUnits;
    console.log('Before update:', layoutCache[field]);
    // Update in-memory cache
    layoutCache[field] = { x1, y1, x2, y2 }; 

    // Apply styles to DOM
    el.style.left   = x1 + 'px';
    el.style.top    = y1 + 'px';
    el.style.width  = (x2 - x1) + 'px';
    el.style.height = (y2 - y1) + 'px';
  });

  console.groupEnd();
}

document.addEventListener('DOMContentLoaded', function() {
  // Initialize GRID_SIZE before layout actions
  initLayout();

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

    $('.draggable-field').resizable({
      handles: 'n, e, s, w, ne, se, sw, nw',
      create: function() {
        console.log('Resizable created for', $(this).data('field'));  // Fires when resizable initialized per field
      },
      start: function(e, ui) {
        const f = $(this).data('field');
        console.log('Resize start for', f, 'position:', ui.position, 'size:', ui.size);
      },
      stop: function(e, ui) {
        const f = $(this).data('field');
        console.group('🔚 Resize stop for', f);
        console.log('Before cache:', layoutCache[f]);
        layoutCache[f] = {
          x1: ui.position.left,
          y1: ui.position.top,
          x2: ui.position.left + ui.size.width,
          y2: ui.position.top  + ui.size.height
        };
        console.log('After cache:', layoutCache[f]);
        const rect = layoutCache[f];
        const hasOverlap = Object.entries(layoutCache).some(([other, r]) =>
          other !== f && intersects(rect, r)
        );
        console.log(`Overlap? ${hasOverlap} for ${f}`);
        if (hasOverlap) {
          console.log(`Reverting ${f} due to overlap`);
          revertPosition(event.target);
        }
        console.groupEnd();
      },
      grid: [GRID_SIZE, GRID_SIZE]
    }).draggable({
      containment: '#layout-grid',
      grid: [GRID_SIZE, GRID_SIZE],
      cancel: '.ui-resizable-handle',
      start: function(e, ui) {
        const f = $(this).data('field');
        console.log('Drag start for', f, 'position:', ui.position);
      }, 
      stop: function(e, ui) {
        const f = $(this).data('field');
        console.group('🔚 Drag stop for', f);
        console.log('Before cache:', layoutCache[f]);
        layoutCache[f] = {
          x1: ui.position.left,
          y1: ui.position.top,
          x2: ui.position.left + $(this).width(),
          y2: ui.position.top  + $(this).height()
        };
        console.log('After cache:', layoutCache[f]);
        const rect = layoutCache[f];
        const hasOverlap = Object.entries(layoutCache).some(([other, r]) =>
          other !== f && intersects(rect, r)
        );
        console.log(`Overlap? ${hasOverlap} for ${f}`);
        if (hasOverlap) {
          console.log(`Reverting ${f} due to overlap`);
          revertPosition(event.target);
        }
        console.groupEnd();
      }
    });    

    console.log('Initial layoutCache:', layoutCache);  // Fires on entering edit mode; shows starting coordinates
  });

  // Save layout changes to the server
  saveLayoutBtn.addEventListener('click', function() {
    // Destroy jQuery UI behaviors
    $('.draggable-field').resizable('destroy').draggable('destroy');
    // Toggle buttons
    toggleEditLayoutBtn.classList.remove('hidden');
    layoutGrid.classList.remove('editing');

    // Build payload from in-memory cache, filtering hidden fields
    const table = layoutGrid.dataset.table;
    const payload = {
      layout: Object.entries(layoutCache)
        .filter(([field]) => document.querySelector(`.draggable-field[data-field="${field}"]`))
        .map(([field, rect]) => ({ field, x1: rect.x1, y1: rect.y1, x2: rect.x2, y2: rect.y2 }))
    };

    console.log('Payload being sent:', JSON.stringify(payload, null, 2));  // Fires before network call; verify structure & values

    fetch(`/${table}/layout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(response => {
      console.log('Server response status:', response.status);           // Fires on HTTP response; check status code
      return response.json();
    })
    .then(data => {
      console.log('Save result:', data);                                // Fires after parsing JSON; inspect 'updated' field
      // Hide buttons
      resetLayoutBtn.classList.add('hidden');
      saveLayoutBtn.classList.add('hidden');
      addFieldBtn.classList.remove('hidden');
    })
    .catch(error => console.error('Save layout failed:', error));         // Fires on network or JSON errors
  });

  resetLayoutBtn.addEventListener('click', reset_layout);

  // Delegated listener for resize handles
  layoutGrid.addEventListener('mousedown', function(e) {
    const handle = e.target.closest('.ui-resizable-handle');
    if (!handle) return;
    const direction = Array.from(handle.classList)
      .find(c => c.startsWith('ui-resizable-') && c !== 'ui-resizable-handle');
    const field     = handle.closest('.draggable-field').dataset.field;
    console.log(`Resize handle clicked: field=${field}, direction=${direction}`);  // Fires on handle mousedown
  });

  // Delegated listener for field click (drag start)
  layoutGrid.addEventListener('mousedown', function(e) {
    if (e.target.closest('.ui-resizable-handle')) return;  // skip handle clicks
    const fieldEl = e.target.closest('.draggable-field');
    if (!fieldEl) return;
    const field = fieldEl.dataset.field;
    console.log(`Field clicked for drag: ${field}`);            // Fires on field mousedown outside handles
  });
});

