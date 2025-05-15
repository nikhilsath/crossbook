document.addEventListener("DOMContentLoaded", () => {
    const fieldTypeSelect = document.getElementById("field_type");
    const optionsContainer = document.getElementById("field-options-container");
    const fkSelectContainer = document.getElementById("fk-select-container");
  
    if (!fieldTypeSelect) return;
  
    fieldTypeSelect.addEventListener("change", () => {
      const type = fieldTypeSelect.value;
  
      if (optionsContainer) {
        if (type === "select" || type === "multi_select") {
          optionsContainer.classList.remove("hidden");
        } else {
          optionsContainer.classList.add("hidden");
        }
      }
  
      if (fkSelectContainer) {
        if (type === "foreign_key") {
          fkSelectContainer.classList.remove("hidden");
        } else {
          fkSelectContainer.classList.add("hidden");
        }
      }
    });
  });
  