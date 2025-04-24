document.addEventListener("DOMContentLoaded", () => {
  const GRID_SIZE = 40; // Size of each grid unit in pixels
  let editMode = false;

  const layoutCache = {};        // Tracks last valid positions
  const initialLayout = {};      // Snapshot of original layout

  const editBtn = document.getElementById('toggle-edit-layout');
  const resetBtn = document.getElementById('reset-layout');

  // Read element metrics and convert to grid units
  function getGridData(el) {
    const rawX = parseFloat(el.getAttribute('data-x')) || 0;
    const rawY = parseFloat(el.getAttribute('data-y')) || 0;
    const width = el.offsetWidth;
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

  // Restore element to last valid spot from layoutCache
  function revertPosition(el) {
    const cfg = layoutCache[el.dataset.field];
    console.log(`⚠️ revertPosition on: ${el.dataset.field}`, cfg);
    if (!cfg) return;
    el.style.transform = `translate(${cfg.x * GRID_SIZE}px, ${cfg.y * GRID_SIZE}px)`;
    el.style.width     = `${cfg.w * GRID_SIZE}px`;
    el.style.height    = `${cfg.h * GRID_SIZE}px`;
    el.setAttribute('data-x', cfg.x * GRID_SIZE);
    el.setAttribute('data-y', cfg.y * GRID_SIZE);
  }

  // Check for overlap after move/resize
  function intersect(a, b) {
    return (
      a.x < b.x + b.w &&
      a.x + a.w > b.x &&
      a.y < b.y + b.h &&
      a.y + a.h > b.y
    );
  }

  function validatePosition(movedEl) {
    const moved = getGridData(movedEl);
    const ok = !Array.from(document.querySelectorAll('.draggable-field')).some(el => {
      if (el === movedEl) return false;
      const other = getGridData(el);
      return intersect(moved, other);
    });
    console.log(`🔍 validatePosition for: ${movedEl.dataset.field} => ${ok}`);
    return ok;
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

  // Enable interact.js behaviors
  function enableLayoutEditing() {
    console.log('🟢 Enabling layout editing');
    // Cache initial positions
    document.querySelectorAll('.draggable-field').forEach(el => updateCache(el));
    Object.assign(initialLayout, JSON.parse(JSON.stringify(layoutCache)));

    interact('.draggable-field')
      .draggable({
        modifiers: [
          interact.modifiers.snap({
            targets: [interact.snappers.grid({ x: GRID_SIZE, y: GRID_SIZE })],
            range: Infinity,
            relativePoints: [{ x: 0, y: 0 }]
          }),
          interact.modifiers.restrictRect({
            restriction: '#layout-grid', endOnly: true
          })
        ],
        inertia: true,
        listeners: {
          move(event) {
            const target = event.target;
            const x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
            const y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
            console.log('🟢 Dragging', target.dataset.field, { dx: event.dx, dy: event.dy });
            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
          },
          end(event) {
            const ok = validatePosition(event.target);
            console.log('🔵 Drag end for', event.target.dataset.field, 'valid?', ok);
            if (!ok) revertPosition(event.target);
            else {
              updateCache(event.target);
              setTimeout(captureAllLayout, 10);
            }
          }
        }
      })
      .resizable({
        edges: { top: true, left: true, bottom: true, right: true },
        modifiers: [
          interact.modifiers.snapSize({ targets: [interact.snappers.grid({ width: GRID_SIZE, height: GRID_SIZE })] }),
          interact.modifiers.restrictSize({ min: { width: GRID_SIZE*4, height: GRID_SIZE*1 } })
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
            console.log('🟢 Resizing', target.dataset.field, { dw: event.deltaRect.width, dh: event.deltaRect.height });
            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
          },
          end(event) {
            const ok = validatePosition(event.target);
            console.log('🔵 Resize end for', event.target.dataset.field, 'valid?', ok);
            if (!ok) revertPosition(event.target);
            else {
              updateCache(event.target);
              setTimeout(captureAllLayout, 10);
            }
          }
        }
      });
  }

  // Disable interact.js behaviors
  function disableLayoutEditing() {
    console.log('🔴 Disabling layout editing');
    interact('.draggable-field').unset();
  }

  // Restore original snapshot
  function resetLayout() {
    console.log('🟡 Resetting layout');
    Object.values(initialLayout).forEach(cfg => {
      const el = document.querySelector(`.draggable-field[data-field="${cfg.field}"]`);
      if (!el) return;
      el.style.transform = `translate(${cfg.x*GRID_SIZE}px, ${cfg.y*GRID_SIZE}px)`;
      el.style.width     = `${cfg.w*GRID_SIZE}px`;
      el.style.height    = `${cfg.h*GRID_SIZE}px`;
      el.setAttribute('data-x', cfg.x*GRID_SIZE);
      el.setAttribute('data-y', cfg.y*GRID_SIZE);
      layoutCache[cfg.field] = { ...cfg };
    });
    console.log('✅ Layout reset complete');
  }

  // Toggle handlers
  editBtn.addEventListener('click', () => {
    console.log('🔘 Toggled edit mode:', !editMode);
    if (!editMode) {
      enableLayoutEditing();
      resetBtn.classList.remove('hidden');
      editBtn.textContent = 'Stop Editing';
    } else {
      disableLayoutEditing();
      resetBtn.classList.add('hidden');
      editBtn.textContent = 'Edit Layout';
    }
    editMode = !editMode;
  });

  resetBtn.addEventListener('click', resetLayout);
});
