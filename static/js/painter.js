// painter.js
// Renders tile previews, highlights, and applies final grid placements

import Grid from './grid.js';

// Single ghost overlay element used during drag
let ghost = null;
let gridInstance = null;

/**
 * Ensure Grid instance is initialized
 * @param {HTMLElement} container
 */
function ensureGrid(container) {
  if (!gridInstance) {
    gridInstance = new Grid('#layout-grid', { columns: 12 });
  }
  return gridInstance;
}

/**
 * Create a translucent clone of the tile for live preview
 * @param {HTMLElement} tileEl
 * @param {HTMLElement} container
 */
export function createGhost(tileEl, container) {
  ensureGrid(container);
  if (ghost) container.removeChild(ghost);
  ghost = tileEl.cloneNode(true);
  ghost.style.pointerEvents = 'none';
  ghost.style.opacity = '0.4';
  ghost.style.position = 'absolute';
  ghost.style.transform = 'none';
  // Preserve grid placement
  ghost.style.gridColumn = tileEl.style.gridColumn;
  ghost.style.gridRow    = tileEl.style.gridRow;
  container.appendChild(ghost);
  return ghost;
}

/**
 * Update the ghost's grid placement
 * @param {HTMLElement} ghostEl
 * @param {number} x  zero-based column index
 * @param {number} y  zero-based row index
 * @param {number} w  width in cells
 * @param {number} h  height in cells
 */
export function updateGhost(ghostEl, x, y, w, h) {
  ensureGrid();
  ghostEl.style.gridColumn = gridInstance.gridColumn(x, w);
  ghostEl.style.gridRow    = gridInstance.gridRow(y, h);
}

/**
 * Remove the ghost preview from the container
 * @param {HTMLElement} container
 */
export function removeGhost(container) {
  if (ghost && container.contains(ghost)) {
    container.removeChild(ghost);
  }
  ghost = null;
}

/**
 * Apply final grid placement to a tile element
 * @param {HTMLElement} tileEl
 * @param {number} x
 * @param {number} y
 * @param {number} w
 * @param {number} h
 */
export function applyPlacement(tileEl, x, y, w, h) {
  ensureGrid();
  tileEl.style.gridColumn = gridInstance.gridColumn(x, w);
  tileEl.style.gridRow    = gridInstance.gridRow(y, h);
  // clear any transforms
  tileEl.style.transform = '';
  tileEl.removeAttribute('data-x');
  tileEl.removeAttribute('data-y');
}

/**
 * Highlight a rectangular cell area (e.g., to show valid drop zone)
 * @param {HTMLElement} container
 * @param {number} x
 * @param {number} y
 * @param {number} w
 * @param {number} h
 */
export function highlightArea(container, x, y, w, h) {
  ensureGrid(container);
  clearHighlights(container);
  const gap = gridInstance.gap;
  const cell = gridInstance.cellSize;

  const overlay = document.createElement('div');
  overlay.classList.add('area-highlight');
  overlay.style.position = 'absolute';
  overlay.style.left   = `${x * (cell + gap)}px`;
  overlay.style.top    = `${y * (cell + gap)}px`;
  overlay.style.width  = `${w * cell + (w - 1) * gap}px`;
  overlay.style.height = `${h * cell + (h - 1) * gap}px`;
  container.appendChild(overlay);
}

/**
 * Remove any existing highlights
 * @param {HTMLElement} container
 */
export function clearHighlights(container) {
  Array.from(container.querySelectorAll('.area-highlight')).forEach(el => container.removeChild(el));
}
