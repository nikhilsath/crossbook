document.addEventListener("DOMContentLoaded", () => {
  const checkboxes = () => document.querySelectorAll(".column-toggle");

  const getSelectedFields = () =>
    Array.from(checkboxes())
      .filter(cb => cb.checked)
      .map(cb => cb.value);

  const updateVisibility = () => {
    const visible = new Set(getSelectedFields());

    document.querySelectorAll("thead th").forEach((th) => {
      if (th.dataset.static !== undefined) return;
      const field = th.textContent.trim();
      th.style.display = visible.has(field) ? "" : "none";
    });

    document.querySelectorAll("tbody tr").forEach(row => {
      row.querySelectorAll("td").forEach(td => {
        if (td.dataset.static !== undefined) return;
        const field = td.dataset.field;
        td.style.display = visible.has(field) ? "" : "none";
      });
    });
  };

  document.getElementById("toggle-columns").addEventListener("click", (e) => {
    e.stopPropagation();
    document.getElementById("column-dropdown").classList.toggle("hidden");
  });

  document.addEventListener("click", () => {
    document.getElementById("column-dropdown").classList.add("hidden");
  });

  document.getElementById("column-dropdown").addEventListener("click", (e) => {
    e.stopPropagation();
  });

  // Attach listeners
  checkboxes().forEach(cb => cb.addEventListener("change", updateVisibility));

  // Initial update
  updateVisibility();
});
