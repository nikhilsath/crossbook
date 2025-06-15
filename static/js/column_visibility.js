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
      const span = th.querySelector("span");
      const field = span ? span.textContent.trim() : th.textContent.trim();
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
  // Attach listeners
  checkboxes().forEach(cb =>
    cb.addEventListener("change", () => {
      updateVisibility();
    })
  );

  // Initial update
  updateVisibility();
});
