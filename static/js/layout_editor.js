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
  boolean: 2,
  number: 2,
  multi_select: 3
};
let GRID_SIZE;

function initLayout() {
  // Grab the container we absolutely position into
  const layoutGrid = document.getElementById('layout-grid');
  // Compute the gap between columns
  const gap = parseInt(getComputedStyle(layoutGrid).columnGap) || 0;
    // Calculate one column’s pixel width
    GRID_SIZE = Math.floor(
      (layoutGrid.clientWidth - gap * (GRID_COLS - 1)) / GRID_COLS
    );
  }

function snapToGrid(value, gridSize) {
  return Math.round(value / gridSize) * gridSize;
}

function buildOccupiedGrid() {
  const grid = {};
  Object.entries(layoutCache).forEach(([field, rect]) => {
    for (let x = rect.x1; x < rect.x2; x++) {
      for (let y = rect.y1; y < rect.y2; y++) {
        grid[`${x},${y}`] = field;
      }
    }
  });
  return grid;
}

function collisionDetection(field) {
  const grid = buildOccupiedGrid();
  const { x1, y1, x2, y2 } = layoutCache[field];
  for (let x = x1; x < x2; x++) {
    for (let y = y1; y < y2; y++) {
      const occupant = grid[`${x},${y}`];
      if (occupant && occupant !== field) {
        return true;
      }
    }
  }
  return false;
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
  // Ensure GRID_SIZE is initialized before any layout actions
  initLayout();

  const toggleEditLayoutBtn = document.getElementById('toggle-edit-layout');
  const resetLayoutBtn      = document.getElementById('reset-layout');
  const addFieldBtn         = document.getElementById('add-field');
  const saveLayoutBtn       = document.getElementById('save-layout');

  // Enter edit mode
  toggleEditLayoutBtn.addEventListener('click', function() {
    resetLayoutBtn.classList.remove('hidden');
    saveLayoutBtn.classList.remove('hidden');
    addFieldBtn.classList.add('hidden');
    toggleEditLayoutBtn.classList.add('hidden');
  });

  // Save layout changes to the server
  saveLayoutBtn.addEventListener('click', function() {
    // Toggle back the Edit Layout button
    toggleEditLayoutBtn.classList.remove('hidden');

    // Build payload from in-memory cache
    const layoutGrid = document.getElementById('layout-grid');
    const table = layoutGrid.dataset.table;
    const payload = {
      layout: Object.entries(layoutCache).map(([field, rect]) => ({
        field,
        x1: rect.x1,
        y1: rect.y1,
        x2: rect.x2,
        y2: rect.y2
      }))
    };

    fetch(`/${table}/layout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
      console.log('Layout saved:', data);
      // Optionally hide save/reset buttons
      resetLayoutBtn.classList.add('hidden');
      saveLayoutBtn.classList.add('hidden');
      addFieldBtn.classList.remove('hidden');
    })
    .catch(error => console.error('Save layout failed:', error));
  });

  // Restore defaults
  resetLayoutBtn.addEventListener('click', reset_layout);
});
