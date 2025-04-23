document.addEventListener("DOMContentLoaded", () => {
    interact('.draggable-field')
      .draggable({
        modifiers: [
          interact.modifiers.snap({
            targets: [interact.snappers.grid({ x: 40, y: 40 })],
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
      .resizable({
        edges: { top: true, left: true, bottom: true, right: true },
        modifiers: [
          interact.modifiers.snapSize({
            targets: [interact.snappers.grid({ width: 40, height: 40 })]
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
  });
  