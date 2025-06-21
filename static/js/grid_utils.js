export function intersects(a, b) {
  return (
    a.colStart < b.colStart + b.colSpan &&
    b.colStart < a.colStart + a.colSpan &&
    a.rowStart < b.rowStart + b.rowSpan &&
    b.rowStart < a.rowStart + a.rowSpan
  );
}

export function revertPosition(el, layout) {
  const prev = el._prevRect;
  if (!prev) return;
  const { colStart, colSpan, rowStart, rowSpan } = prev;
  el.style.gridColumn = `${colStart} / span ${colSpan}`;
  el.style.gridRow = `${rowStart} / span ${rowSpan}`;
  el.style.left = '';
  el.style.top = '';
  el.style.width = '';
  el.style.height = '';
  el.style.position = '';
  if (layout) {
    const key = el.dataset.field || el.dataset.widget;
    if (key) layout[key] = { ...prev };
  }
}
