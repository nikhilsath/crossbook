document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn  = document.getElementById("toggle-filters");
    const dropdown   = document.getElementById("filter-dropdown");
  
    // Get currently visible columns (same as column_visibility.js)
    const getSelectedFields = () =>
      Array.from(document.querySelectorAll(".column-toggle"))
           .filter(cb => cb.checked)
           .map(cb => cb.value);
  
    // Called whenever a filter‐toggle box is changed
    function updateFilters() {
      const params = new URLSearchParams(window.location.search);
  
      // Remove existing filter params for ALL visible fields
      getSelectedFields().forEach(f => params.delete(f));
  
      // Add back only the ones currently checked
      Array.from(dropdown.querySelectorAll(".filter-toggle"))
        .filter(cb => cb.checked)
        .forEach(cb => params.set(cb.value, ""));
  
      // Reload with updated params
      window.location.search = params.toString();
    }
  
    // Build the dropdown checkbox list
    function populateFilterDropdown() {
      dropdown.innerHTML = "";
      const params = new URLSearchParams(window.location.search);
  
      getSelectedFields().forEach(field => {
        const label = document.createElement("label");
        label.classList.add("flex","items-center","space-x-2");
  
        const input = document.createElement("input");
        input.type = "checkbox";
        input.classList.add("filter-toggle");
        input.value = field;
        if (params.has(field)) input.checked = true;
  
        // <-- now this can see updateFilters()
        input.addEventListener("change", updateFilters);
  
        const span = document.createElement("span");
        span.classList.add("text-sm");
        span.textContent = field;
  
        label.append(input, span);
        dropdown.append(label);
      });
    }
  
    // Wire up dropdown toggling
    toggleBtn.addEventListener("click", e => {
      e.stopPropagation();
      dropdown.classList.toggle("hidden");
      populateFilterDropdown();
    });
    document.addEventListener("click", () => dropdown.classList.add("hidden"));
    dropdown.addEventListener("click", e => e.stopPropagation());
  
    // Rebuild filters list whenever columns change
    document.querySelectorAll(".column-toggle").forEach(cb => {
      cb.addEventListener("change", () => setTimeout(populateFilterDropdown, 0));
    });
  });
  