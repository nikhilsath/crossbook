// layout_editor.js
import Sortable from "https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/modular/sortable.esm.js";

let layoutMode = false;

export function toggleLayoutMode(containerSelector, tableName) {
  layoutMode = !layoutMode;
  const container = document.querySelector(containerSelector);
  container.classList.toggle("ring-2", layoutMode);
  container.classList.toggle("ring-blue-400", layoutMode);

  if (layoutMode) {
    activateSortable(container, tableName);
    activateResizeHandles(container, tableName);
  } else {
    location.reload();
  }
}

function activateSortable(container, tableName) {
  const items = Array.from(container.children);

  new Sortable(container, {
    animation: 150,
    ghostClass: "bg-yellow-100",
    onEnd: function () {
      saveLayout(container, tableName);
    }
  });

  items.forEach((el) => {
    el.style.cursor = "grab";
    el.style.border = "1px dashed #ccc";
    el.style.padding = "0.5rem";
    el.style.position = "relative";
  });
}

function activateResizeHandles(container, tableName) {
  const items = container.querySelectorAll("[data-field-name]");

  items.forEach(el => {
    const hHandle = document.createElement("div");
    hHandle.className = "resize-handle horizontal";
    Object.assign(hHandle.style, {
      width: "6px",
      height: "100%",
      cursor: "ew-resize",
      position: "absolute",
      top: "0",
      right: "0",
      zIndex: "10",
      backgroundColor: "rgba(0,0,0,0.1)"
    });

    const vHandle = document.createElement("div");
    vHandle.className = "resize-handle vertical";
    Object.assign(vHandle.style, {
      height: "6px",
      width: "100%",
      cursor: "ns-resize",
      position: "absolute",
      bottom: "0",
      left: "0",
      zIndex: "10",
      backgroundColor: "rgba(0,0,0,0.1)"
    });

    el.appendChild(hHandle);
    el.appendChild(vHandle);

    let startX, startY, startWidth, startHeight;

    hHandle.addEventListener("mousedown", e => {
      e.preventDefault();
      startX = e.clientX;
      startWidth = el.offsetWidth;
      document.documentElement.style.cursor = "ew-resize";

      const onMove = (e) => {
        const newWidth = Math.max(100, startWidth + (e.clientX - startX));
        el.style.width = `${newWidth}px`;
      };

      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        document.documentElement.style.cursor = "";
        saveLayout(container, tableName);
      };

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });

    vHandle.addEventListener("mousedown", e => {
      e.preventDefault();
      startY = e.clientY;
      startHeight = el.offsetHeight;
      document.documentElement.style.cursor = "ns-resize";

      const onMove = (e) => {
        const newHeight = Math.max(40, startHeight + (e.clientY - startY));
        el.style.height = `${newHeight}px`;
      };

      const onUp = () => {
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        document.documentElement.style.cursor = "";
        saveLayout(container, tableName);
      };

      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    });
  });
}

function snapWidth(px, containerWidth) {
  const grid = [0.25, 0.33, 0.5, 0.66, 0.75, 1];
  const ratio = px / containerWidth;
  const closest = grid.reduce((a, b) => Math.abs(b - ratio) < Math.abs(a - ratio) ? b : a);
  return `${Math.round(closest * 100)}%`;
}

function snapHeight(px) {
  return `${Math.round(px / 50) * 50}px`;
}

function saveLayout(container, tableName) {
  const containerWidth = container.offsetWidth || 800;

  const updates = Array.from(container.children).map((el, index) => {
    const fieldName = el.dataset.fieldName;
    if (!fieldName) return null;

    const widthPx = el.offsetWidth;
    const heightPx = el.offsetHeight;

    const width = snapWidth(widthPx, containerWidth);
    const minWidth = el.style.minWidth || "200px";
    const height = snapHeight(heightPx);

    return {
      field: fieldName,
      layout: {
        width,
        minWidth,
        height,
        row: 1,
        col: index + 1
      }
    };
  }).filter(Boolean);

  fetch(`/${tableName}/layout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates)
  }).then(() => console.log("Layout saved"));
  
  updates.forEach(u => {
    const el = container.querySelector(`[data-field-name="${u.field}"]`);
    if (el) {
      el.style.width = u.layout.width;
      el.style.height = u.layout.height;
    }
  });
  
}
