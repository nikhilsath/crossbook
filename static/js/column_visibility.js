document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("column-visibility");
    if (!select) return;
  
    const getSelectedFields = () =>
      Array.from(select.selectedOptions).map(opt => opt.value);
  
    const updateVisibility = () => {
      const visible = new Set(getSelectedFields());
  
      // Update <th>
      document.querySelectorAll("thead th").forEach((th, idx) => {
        const field = th.textContent.trim().toLowerCase();
        th.style.display = visible.has(field) ? "" : "none";
      });
  
      // Update <td>
      document.querySelectorAll("tbody tr").forEach(row => {
        row.querySelectorAll("td").forEach((td, idx) => {
          const field = td.dataset.field;
          td.style.display = visible.has(field) ? "" : "none";
        });
      });
    };
  
    select.addEventListener("change", updateVisibility);
    updateVisibility(); // run once on load
  });
  