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
  } else {
    location.reload(); // Reload to exit edit mode cleanly
  }
}

function activateSortable(container, tableName) {
  const items = Array.from(container.children);

  new Sortable(container, {
    animation: 150,
    ghostClass: "bg-yellow-100",
    onEnd: function () {
      const updates = items.map((el, index) => {
        const fieldName = el.querySelector('[data-field-name]')?.dataset.fieldName;
        if (!fieldName) return null;
        const width = el.style.width || "100%";
        const minWidth = el.style.minWidth || "200px";
        return { field: fieldName, layout: { width, minWidth, row: 1, col: index + 1 } };
      }).filter(Boolean);

      fetch(`/${tableName}/layout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates)
      }).then(() => console.log("Layout saved"));
    }
  });

  // Add visual cues and drag handles
  items.forEach((el) => {
    el.style.cursor = "grab";
    el.style.border = "1px dashed #ccc";
    el.style.padding = "0.5rem";
  });
}
