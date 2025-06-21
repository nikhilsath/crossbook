const defaultWidgetWidth = {
  value: 4,
  table: 10,
  chart: 10
};

const defaultWidgetHeight = {
  value: 3,
  table: 8,
  chart: 12
};

const widgetLayout = window.WIDGET_LAYOUT || {};
window.removeDashboardWidget = function(id) {
  delete widgetLayout[id];
};

function enterEditMode() {
  const grid = document.getElementById('dashboard-grid');
  if (grid) {
    grid.classList.add('editing');
  }
  document
    .querySelectorAll('#dashboard-grid .resize-handle')
    .forEach(h => h.classList.remove('hidden'));
  const saveBtn = document.getElementById('dashboard_save');
  if (saveBtn) saveBtn.classList.remove('hidden');
  const editBtn = document.getElementById('dashboard_edit');
  if (editBtn) editBtn.classList.add('hidden');
}

function exitEditMode() {
  const grid = document.getElementById('dashboard-grid');
  if (grid) {
    grid.classList.remove('editing');
  }
  document
    .querySelectorAll('#dashboard-grid .resize-handle')
    .forEach(h => h.classList.add('hidden'));
  const saveBtn = document.getElementById('dashboard_save');
  if (saveBtn) saveBtn.classList.add('hidden');
  const editBtn = document.getElementById('dashboard_edit');
  if (editBtn) editBtn.classList.remove('hidden');
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
  if (!prev) return;
  el.style.gridColumn = `${prev.colStart} / span ${prev.colSpan}`;
  el.style.gridRow    = `${prev.rowStart} / span ${prev.rowSpan}`;
  el.style.left = '';
  el.style.top  = '';
  el.style.position = '';
  widgetLayout[el.dataset.widget] = { ...prev };
}

function saveDashboardLayout() {
  const layout = Object.entries(widgetLayout).map(([id, rect]) => ({
    id: parseInt(id),
    colStart: rect.colStart,
    colSpan: rect.colSpan,
    rowStart: rect.rowStart,
    rowSpan: rect.rowSpan
  }));
  fetch('/dashboard/layout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ layout })
  })
    .then(res => res.json())
    .then(data => { console.debug('[dashboard] save layout', data); })
    .catch(err => { console.error('[dashboard] save layout error', err); });
}

function enableDashboardDrag() {
  const grid = document.getElementById('dashboard-grid');
  let isDragging = false;
  let startX, startY, startRect, widgetEl, widgetId;

  grid.addEventListener('mousedown', e => {
    if (!grid.classList.contains('editing')) return;
    if (e.target.classList.contains('resize-handle')) return;
    widgetEl = e.target.closest('.draggable-field');
    widgetId = widgetEl?.dataset.widget;
    if (!widgetEl || !widgetId) return;
    console.debug('[dashboard] drag start', widgetId);
    widgetEl._prevRect = { ...widgetLayout[widgetId] };
    const rect = widgetEl.getBoundingClientRect();
    widgetEl.style.width  = `${rect.width}px`;
    widgetEl.style.height = `${rect.height}px`;
    const gridRect = grid.getBoundingClientRect();
    startX = e.clientX;
    startY = e.clientY;
    startRect = {
      left:   rect.left - gridRect.left,
      top:    rect.top  - gridRect.top,
      ...widgetLayout[widgetId]
    };
    widgetEl.style.gridColumn = '';
    widgetEl.style.gridRow = '';
    widgetEl.style.position = 'absolute';
    widgetEl.style.left = `${startRect.left}px`;
    widgetEl.style.top  = `${startRect.top}px`;
    isDragging = true;
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });

  function onMove(e) {
    if (!isDragging || !grid.classList.contains('editing')) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    widgetEl.style.left = `${startRect.left + dx}px`;
    widgetEl.style.top  = `${startRect.top  + dy}px`;
  }

  function onUp(e) {
    if (!isDragging) return;
    isDragging = false;
    if (!grid.classList.contains('editing')) {
      revertPosition(widgetEl);
      console.debug('[dashboard] drag revert', widgetId);
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      return;
    }
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const containerWidth = grid.clientWidth;
    const gridCols = 20;
    const gridCellWidth = containerWidth / gridCols;
    const newColStart = Math.floor((startRect.left + dx) / gridCellWidth);
    const rowEm = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const newRowStart = Math.round((startRect.top + dy) / rowEm);
    widgetLayout[widgetId] = {
      colStart: newColStart + 1,
      colSpan:  startRect.colSpan,
      rowStart: newRowStart + 1,
      rowSpan:  startRect.rowSpan
    };
    const hasOverlap = Object.entries(widgetLayout).some(([other, rect]) =>
      other !== widgetId && intersects(widgetLayout[widgetId], rect)
    );
    if (hasOverlap) {
      revertPosition(widgetEl);
      console.debug('[dashboard] drag revert', widgetId);
    } else {
      widgetEl.style.left = '';
      widgetEl.style.top = '';
      widgetEl.style.position = '';
      widgetEl.style.gridColumn = `${newColStart + 1} / span ${startRect.colSpan}`;
      widgetEl.style.gridRow    = `${newRowStart + 1} / span ${startRect.rowSpan}`;
      widgetEl.style.width = '';
      widgetEl.style.height = '';
    }
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
    console.debug('[dashboard] drag end', widgetId, widgetLayout[widgetId]);
  }
}

function enableDashboardResize() {
  const grid = document.getElementById('dashboard-grid');
  const handles = document.querySelectorAll('.resize-handle');
  let isResizing = false;
  let handleType, widgetEl, widgetId, startX, startY, startRect;

  grid.addEventListener('mousedown', e => {
    if (!grid.classList.contains('editing')) return;
    if (!e.target.classList.contains('resize-handle')) return;
    e.preventDefault();
    handleType = ['top-left','top-right','bottom-left','bottom-right']
                   .find(c => e.target.classList.contains(c));
    widgetEl = e.target.closest('.draggable-field');
    widgetId = widgetEl.dataset.widget;
    console.debug('[dashboard] resize start', widgetId, handleType);
    startX = e.clientX;
    startY = e.clientY;
    startRect = { ...widgetLayout[widgetId] };
    widgetEl._prevRect = { ...startRect };
    isResizing = true;
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });

  function onMove(e) {
    if (!isResizing || !grid.classList.contains('editing')) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const containerWidth = grid.clientWidth;
    const gridCols = 20;
    const gridCellWidth = containerWidth / gridCols;
    const deltaCols = Math.round(dx / gridCellWidth);
    const rowEm = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const deltaRows = Math.round(dy / rowEm);

    let { colStart, colSpan, rowStart, rowSpan } = startRect;
    let newColStart = colStart, newRowStart = rowStart;
    let newColSpan = colSpan, newRowSpan = rowSpan;

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

    widgetEl.style.gridColumn = `${newColStart} / span ${newColSpan}`;
    widgetEl.style.gridRow    = `${newRowStart} / span ${newRowSpan}`;
  }

  function onUp() {
    if (!isResizing) return;
    isResizing = false;
    if (!grid.classList.contains('editing')) {
      revertPosition(widgetEl);
      console.debug('[dashboard] resize revert', widgetId);
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      return;
    }
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);

    const partsCol = widgetEl.style.gridColumn.split(' ');
    const partsRow = widgetEl.style.gridRow.split(' ');
    const newRect = {
      colStart: parseInt(partsCol[0]),
      colSpan:  parseInt(partsCol[3]),
      rowStart: parseInt(partsRow[0]),
      rowSpan:  parseInt(partsRow[3])
    };
    const hasOverlap = Object.entries(widgetLayout).some(([id, rect]) =>
      id !== widgetId && intersects(newRect, rect)
    );
    if (hasOverlap) {
      revertPosition(widgetEl);
      console.debug('[dashboard] resize revert', widgetId);
    } else {
      widgetLayout[widgetId] = newRect;
    }
    console.debug('[dashboard] resize end', widgetId, widgetLayout[widgetId]);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  enableDashboardDrag();
  enableDashboardResize();
  const editBtn = document.getElementById('dashboard_edit');
  if (editBtn) editBtn.addEventListener('click', enterEditMode);
  const saveBtn = document.getElementById('dashboard_save');
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      saveDashboardLayout();
      exitEditMode();
    });
  }
});
