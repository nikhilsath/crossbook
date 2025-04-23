document.addEventListener("DOMContentLoaded", () => {
    const GRID_SIZE = 40; // Size of each grid unit in pixels
    const layoutCache = {}; // Track previous valid layout

    interact('.draggable-field')
      .draggable({
        modifiers: [
          interact.modifiers.snap({
            targets: [interact.snappers.grid({ x: GRID_SIZE, y: GRID_SIZE })],
            range: Infinity,
            relativePoints: [{ x: 0, y: 0 }]
          }),
          interact.modifiers.restrictRect({
            restriction: '#layout-grid',
            endOnly: true
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
            if (!validatePosition(event.target)) {
              revertPosition(event.target);
            } else {
              updateCache(event.target);
              setTimeout(captureAllLayout, 10);
            }
          }
        }
      })

      .resizable({
        edges: { top: true, left: true, bottom: true, right: true },
        modifiers: [
          interact.modifiers.snapSize({
            targets: [interact.snappers.grid({ width: GRID_SIZE, height: GRID_SIZE })]
          }),
          interact.modifiers.restrictSize({
            min: { width: GRID_SIZE * 4, height: GRID_SIZE * 1 }
          })
        ],
        listeners: {
          move(event) {
            const target = event.target;
            let x = parseFloat(target.getAttribute('data-x')) || 0;
            let y = parseFloat(target.getAttribute('data-y')) || 0;

            target.style.width = `${event.rect.width}px`;
            target.style.height = `${event.rect.height}px`;

            x += event.deltaRect.left;
            y += event.deltaRect.top;

            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
          },
          end(event) {
            if (!validatePosition(event.target)) {
              revertPosition(event.target);
            } else {
              updateCache(event.target);
              setTimeout(captureAllLayout, 10);
            }
          }
        }
      });

    function getGridData(el) {
      const rawX = parseFloat(el.getAttribute('data-x')) || 0;
      const rawY = parseFloat(el.getAttribute('data-y')) || 0;
      const width = el.offsetWidth;
      const height = el.offsetHeight;

      const x = Math.round(rawX / GRID_SIZE);
      const y = Math.round(rawY / GRID_SIZE);
      const w = Math.round(width / GRID_SIZE);
      const h = Math.round(height / GRID_SIZE);

      return {
        field: el.dataset.field,
        x,
        y,
        w,
        h
      };
    }

    function updateCache(el) {
      const data = getGridData(el);
      layoutCache[data.field] = { ...data };
    }

    function revertPosition(el) {
      const field = el.dataset.field;
      const data = layoutCache[field];
      if (data) {
        el.style.transform = `translate(${data.x * GRID_SIZE}px, ${data.y * GRID_SIZE}px)`;
        el.style.width = `${data.w * GRID_SIZE}px`;
        el.style.height = `${data.h * GRID_SIZE}px`;
        el.setAttribute('data-x', data.x * GRID_SIZE);
        el.setAttribute('data-y', data.y * GRID_SIZE);
      }
    }

    function validatePosition(movedEl) {
      const moved = getGridData(movedEl);
      return !Array.from(document.querySelectorAll('.draggable-field')).some(el => {
        if (el === movedEl) return false;
        const other = getGridData(el);
        return intersect(moved, other);
      });
    }

    function intersect(a, b) {
      return (
        a.x < b.x + b.w &&
        a.x + a.w > b.x &&
        a.y < b.y + b.h &&
        a.y + a.h > b.y
      );
    }

    function captureAllLayout() {
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
        .catch(err => {
          console.error('❌ Layout save error:', err);
        });
    }

    // Cache all field positions on load
    document.querySelectorAll('.draggable-field').forEach(updateCache);
});