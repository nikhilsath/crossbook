document.addEventListener("DOMContentLoaded", () => {
    const GRID_SIZE = 40; // Size of each grid unit in pixels

    // Make fields draggable
    interact('.draggable-field')
      .draggable({
        modifiers: [
          interact.modifiers.snap({
            targets: [interact.snappers.grid({ x: GRID_SIZE, y: GRID_SIZE })],
            range: Infinity,
            relativePoints: [{ x: 0, y: 0 }]
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

      // Make fields resizable
      .resizable({
        edges: { top: true, left: true, bottom: true, right: true },
        modifiers: [
          interact.modifiers.snapSize({
            targets: [interact.snappers.grid({ width: GRID_SIZE, height: GRID_SIZE })]
          })
        ],
        listeners: {
          move(event) {
            const target = event.target;
            let x = parseFloat(target.getAttribute('data-x')) || 0;
            let y = parseFloat(target.getAttribute('data-y')) || 0;

            // Apply size
            target.style.width = `${event.rect.width}px`;
            target.style.height = `${event.rect.height}px`;

            // Apply new transform offset
            x += event.deltaRect.left;
            y += event.deltaRect.top;

            target.style.transform = `translate(${x}px, ${y}px)`;
            target.setAttribute('data-x', x);
            target.setAttribute('data-y', y);
          }
        }
      });

    function getGridData(el) {
      const x = parseInt(el.getAttribute('data-x')) || 0;
      const y = parseInt(el.getAttribute('data-y')) || 0;
      const width = el.offsetWidth;
      const height = el.offsetHeight;

      return {
        field: el.dataset.field,
        x: Math.round(x / GRID_SIZE),
        y: Math.round(y / GRID_SIZE),
        w: Math.round(width / GRID_SIZE),
        h: Math.round(height / GRID_SIZE)
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

    // Trigger layout save on drag or resize end
    document.addEventListener('mouseup', () => {
      setTimeout(captureAllLayout, 10);
    });
});
