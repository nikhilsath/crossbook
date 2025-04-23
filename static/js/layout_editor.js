document.addEventListener("DOMContentLoaded", () => {
    const GRID_SIZE = 40; // Size of each grid unit in pixels

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

    function captureAllLayout() {
      const layout = [];
      document.querySelectorAll('.draggable-field').forEach(el => {
        layout.push(getGridData(el));
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

    document.addEventListener('mouseup', () => {
      setTimeout(captureAllLayout, 10);
    });
});
